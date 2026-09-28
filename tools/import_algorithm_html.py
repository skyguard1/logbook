#!/usr/bin/env python3
"""DOM-based local HTML import: algorithms, topics, images and redacted metadata."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import struct
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from bs4 import BeautifulSoup, Comment, NavigableString

REPO = Path(__file__).resolve().parents[1]
MANIFEST = Path('tools/algorithm-import-manifest.json')
POSTS = Path('source/_posts/algorithm')
IMAGES = Path('source/images/algorithm')
SELECTORS = ('#mce_view_content', '#article_content', '#text-content', 'div#main-content.wiki-content')
DROP = 'script, style, template, iframe, object, embed, form, input, button, link, meta, base, nav, noscript'
DECORATIONS = re.compile(r'avatar|qr[-_]?code|watermark|has-apply|headline|operations|related[-_]posts|digg_favor', re.I)
INTERNAL = re.compile(r'(?:[a-z0-9-]+\.)*(?:woa\.com|oa\.com|tencent\.com|sogou-inc\.com)', re.I)
INTERNAL_URL = re.compile(r'(?:https?:)?//[^\s<>"\']*(?:woa\.com|oa\.com|tencent\.com|sogou-inc\.com)[^\s<>"\']*', re.I)
COMPANIES = ('腾讯公司', '腾讯云', '腾讯', 'Tencent', '字节跳动', '阿里巴巴', '阿里云', '百度', '搜狗', '美团', '京东', '快手', '脸书', 'Facebook', 'Google', '谷歌', '微软', 'Microsoft', '亚马逊', 'Amazon', '华为', '网易', '鹅厂')
DEPARTMENTS = ('技术工程事业群', '平台与内容事业群', '互动娱乐事业群', '云与智慧产业事业群', '公共研发运营体系', '互娱增值服务部', 'IEG增值服务部', '资金与数据部', '广告平台与产品部', '社交平台部', '数据平台部', '证券产品部', '在线视频产品部', '研发支撑中心', 'AI基础产品中心', '知识挖掘组', '搜索应用部', '技术架构部', '技术能力提升', '技术&服务藏经阁', 'Delta Space', '增量智坊', 'KM平台', '腾讯iWiki')
DEPARTMENTS += (
    '云架构平台部', 'OVBU-平台技术部', '平台技术部', '搜索语义中心',
    '新闻工程研发部', '广告平台产品部', 'AI平台部', '兴趣阅读产品部',
    '新闻技术平台部', '搜索部门', 'Research部门', '云产品部', '算法中心',
    '平台产品技术部', '技术运营部', '微信基础平台部', '基础平台部', '新闻算法中心',
)
GROUPS = re.compile(r'(?<![A-Za-z])(?:WXG|PCG|IEG|OMG|SNG|CSIG|CDG|TEG|CROS|AMS)(?![A-Za-z])', re.I)
TOPICS = (
    ('图学习与知识图谱', r'图谱|GNN|Graph|图卷积|图神经|网络表征|图算法|图技术|实体对齐|社交网络'),
    ('强化学习与决策', r'强化学习|\bRL\b'),
    ('数据科学与评估', r'因果|归因|贝叶斯|XGBoost|异常检测|数据分析|校准'),
    ('特征工程', r'特征|AutoGroup|Auto Feature|Auto Embedding'),
    ('模型训练与推理', r'DeepSpeed|TensorFlow|Tesla|训练|推理|serving|精度|模型生产|模型自动化|全流程|算法平台|无量'),
    ('多模态与自然语言处理', r'多模态|BERT|Transformer|关键词|NLP|时序|内容表示|视频事件'),
    ('推荐与排序', r'推荐|召回|排序|混排|重排|CTR|DSSM|多任务|在线学习|用户行为'),
    ('广告算法', r'广告|流控|库存|售卖|频次'),
    ('数据工程与系统实践', r'Flink|Kafka|数据|微服务|账户|计算|稳定性|系统|框架'),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_files(root: Path) -> list[Path]:
    if not root.is_dir():
        raise ValueError('Source directory does not exist')
    files = sorted(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in {'.html', '.htm'}
                   and p.resolve().is_relative_to(root.resolve())
                   and not p.name.startswith('saved_resource')
                   and not any(x.endswith('_files') for x in p.relative_to(root).parts[:-1]))
    if not files:
        raise ValueError('Source directory contains no article HTML files')
    return files


def local_file(url: str, current: Path, root: Path) -> Path | None:
    """Never fetch URLs or read outside the selected source tree."""
    parts = urlsplit(url)
    if parts.scheme or parts.netloc:
        return None
    path = (current.parent / unquote(parts.path)).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        return None
    return path


def extract(path: Path, root: Path, visited=None):
    visited = set() if visited is None else visited
    if path in visited or len(visited) >= 12:
        return None
    visited.add(path)
    soup = BeautifulSoup(path.read_bytes(), 'html.parser')
    for selector in SELECTORS:
        body = soup.select_one(selector)
        if body and (body.get_text(strip=True) or body.find('img')):
            return body, path
    for frame in soup.find_all('iframe', src=True):
        nested = local_file(frame['src'], path, root)
        if nested and nested.suffix.lower() in {'.html', '.htm'}:
            result = extract(nested, root, visited)
            if result:
                return result
    return None


class Scrubber:
    def __init__(self, files: list[Path]):
        suffixes = {part.strip() for p in files for part in p.stem.split(' - ')[1:] if part.strip()}
        phrases = suffixes | set(DEPARTMENTS) | set(COMPANIES)
        alternatives = []
        for phrase in sorted(phrases, key=lambda x: (-len(x), x)):
            pattern = re.escape(phrase)
            # Do not corrupt imports such as google.protobuf or model names.
            if phrase.isascii() and phrase.isalpha():
                pattern = r'(?<![\w.])' + pattern + r'(?![\w.])'
            alternatives.append(pattern)
        self.pattern = re.compile('|'.join(alternatives), re.I)

    def __call__(self, text: str) -> str:
        text = INTERNAL_URL.sub('[内部链接已移除]', text)
        text = re.sub(r'[\w.+-]+@(?:[\w-]+\.)*(?:tencent|woa|sogou-inc)\.com', '[组织邮箱已移除]', text, flags=re.I)
        return GROUPS.sub('', self.pattern.sub('', text))

    def title(self, path: Path) -> str:
        title = re.sub(r'^[【\[].*?[】\]]\s*', '', path.stem.split(' - ')[0])
        return re.sub(r'\s+', ' ', self(title)).strip(' -_：:') or '算法笔记'


def classify(title: str) -> str:
    return next((topic for topic, pattern in TOPICS if re.search(pattern, title, re.I)), '综合实践')


def site_root(repo: Path) -> str:
    text = (repo / '_config.yml').read_text(encoding='utf-8')
    explicit = re.search(r'^root:\s*([^\n#]+)', text, re.M)
    url = re.search(r'^url:\s*([^\n#]+)', text, re.M)
    value = explicit.group(1).strip().strip('"\'') if explicit else urlsplit(url.group(1).strip().strip('"\'')).path if url else ''
    return '/' + value.strip('/') + '/' if value.strip('/') else '/'


def image_extension(data: bytes) -> str | None:
    for magic, ext in ((b'\x89PNG\r\n\x1a\n', 'png'), (b'\xff\xd8\xff', 'jpg'), (b'GIF87a', 'gif'), (b'GIF89a', 'gif'), (b'BM', 'bmp')):
        if data.startswith(magic):
            return ext
    if data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return 'webp'
    if re.search(br'<svg\b', data[:1024], re.I):
        return 'svg'
    return None


def safe_url(url: str) -> bool:
    return (url.startswith('#') or urlsplit(url).scheme in {'http', 'https'}) and not INTERNAL.search(urlsplit(url).hostname or '')


def clean_dom(body, scrub: Scrubber):
    """Clean individual DOM nodes, never intervening paragraphs."""
    for tag in list(body.select(DROP)):
        if tag.parent:
            tag.decompose()
    for comment in list(body.find_all(string=lambda s: isinstance(s, Comment))):
        comment.extract()
    for tag in list(body.find_all(True)):
        if tag.parent and DECORATIONS.search(' '.join(tag.get('class', [])) + ' ' + str(tag.get('id', ''))):
            tag.decompose()
    for pre in body.find_all('pre'):
        for br in pre.find_all('br'):
            br.replace_with('\n')
        text = pre.get_text()
        pre.clear()
        pre.append(text)
    for span in list(body.find_all(['span', 'font'])):
        span.unwrap()
    body.smooth()
    for tag in list(body.find_all(['p', 'blockquote'])):
        if tag.parent:
            text = tag.get_text(' ', strip=True)
            if re.match(r'^(?:所属部门|部门|团队介绍|所属团队|From)\s*[:：]', text, re.I) or ('K吧' in text and '分享' in text):
                tag.decompose()
    for link in list(body.find_all('a')):
        if not safe_url(str(link.get('href', ''))):
            if link.get_text(strip=True).startswith(('http:', 'https:')):
                link.replace_with('[内部或本地链接已移除]')
            else:
                link.unwrap()
    for node in list(body.find_all(string=True)):
        node.replace_with(NavigableString(scrub(str(node))))
    svg_attrs = {'d', 'viewbox', 'xmlns', 'xmlns:xlink', 'x', 'y', 'x1', 'x2', 'y1', 'y2', 'cx', 'cy', 'r', 'rx', 'ry', 'points', 'transform', 'width', 'height', 'fill', 'stroke', 'stroke-width', 'id', 'href', 'xlink:href', 'preserveaspectratio'}
    math_attrs = {'display', 'mathvariant', 'columnalign', 'rowspacing', 'columnspacing', 'displaystyle'}
    for tag in body.find_all(True):
        in_svg = tag.name == 'svg' or tag.find_parent('svg') is not None
        in_math = tag.name == 'math' or tag.find_parent('math') is not None
        allowed = svg_attrs if in_svg else math_attrs if in_math else {'colspan', 'rowspan'}
        if tag.name == 'a':
            allowed = {'href'}
        if tag.name == 'img':
            allowed = {'src', 'alt', 'loading'}
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in allowed}
        if in_svg:
            for key in ('href', 'xlink:href'):
                if key in tag.attrs and not str(tag[key]).startswith('#'):
                    del tag[key]
            for key in ('fill', 'stroke'):
                if 'url(' in str(tag.get(key, '')) and not str(tag[key]).startswith('url(#'):
                    del tag[key]
            for lower, camel in (('viewbox', 'viewBox'), ('preserveaspectratio', 'preserveAspectRatio')):
                if lower in tag.attrs:
                    tag[camel] = tag.attrs.pop(lower)
        if tag.name == 'img':
            tag['alt'] = scrub(str(tag.get('alt', '图示')))
            tag['loading'] = 'lazy'


def clean_image_bytes(data: bytes, ext: str, scrub: Scrubber) -> bytes:
    if ext == 'svg':
        root = ET.fromstring(data)
        if root.tag.split('}')[-1] != 'svg':
            raise ValueError('Not an SVG image')
        ET.register_namespace('', 'http://www.w3.org/2000/svg')
        ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
        for parent in list(root.iter()):
            for child in list(parent):
                if child.tag.split('}')[-1].lower() in {'script', 'foreignobject', 'iframe', 'metadata'}:
                    parent.remove(child)
        for element in root.iter():
            for key in list(element.attrib):
                name = key.split('}')[-1].lower()
                value = element.attrib[key]
                if name.startswith('on') or (name in {'href', 'src'} and not value.startswith('#')):
                    del element.attrib[key]
                elif any(not url.strip().strip('"\'').startswith('#')
                         for url in re.findall(r'url\(([^)]*)\)', value, re.I)):
                    del element.attrib[key]
            if element.text:
                element.text = scrub(element.text)
            if element.tail:
                element.tail = scrub(element.tail)
        return ET.tostring(root, encoding='utf-8', xml_declaration=True)
    if ext == 'png':
        # Drop ancillary text/EXIF, including oversized compressed metadata.
        # IDAT, palette, transparency and colour-profile chunks remain untouched.
        chunks = [data[:8]]
        offset = 8
        while offset + 12 <= len(data):
            size = struct.unpack('>I', data[offset:offset + 4])[0]
            end = offset + size + 12
            if end > len(data):
                raise ValueError('Truncated PNG chunk')
            kind = data[offset + 4:offset + 8]
            if kind not in {b'tEXt', b'zTXt', b'iTXt', b'eXIf', b'tIME'}:
                chunks.append(data[offset:end])
            if kind == b'IEND':
                return b''.join(chunks)
            offset = end
        raise ValueError('PNG has no IEND chunk')
    return data


def copy_images(body, path: Path, source: Path, stage: Path, root_url: str, scrub: Scrubber, images_root: Path = IMAGES):
    stats = Counter()
    for img in list(body.find_all('img')):
        if not img.parent:
            continue
        if DECORATIONS.search(' '.join(img.get('class', []))):
            img.decompose()
            continue
        stats['image_references'] += 1
        data = None
        for key in ('src', 'data-src', 'data-original'):
            url = str(img.get(key, ''))
            if not url:
                continue
            local = local_file(url, path, source)
            if local:
                data = local.read_bytes()
                break
            if re.match(r'^data:image/(?:png|jpeg|gif|webp);base64,', url, re.I):
                try:
                    data = base64.b64decode(url.split(',', 1)[1], validate=True)
                    break
                except ValueError:
                    pass
        ext = image_extension(data) if data else None
        if not ext:
            stats['missing_images'] += 1
            img.replace_with('[图片未保存到本地]')
            continue
        try:
            data = clean_image_bytes(data, ext, scrub)
        except (ValueError, ET.ParseError):
            stats['invalid_images'] += 1
            img.replace_with('[原始图片文件损坏]')
            continue
        rel = images_root / (digest(data)[:20] + '.' + ext)
        target = stage / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        img.attrs = {'src': root_url + quote(rel.relative_to('source').as_posix()), 'alt': scrub(str(img.get('alt', '图示'))), 'loading': 'lazy'}
        stats['resolved_images'] += 1
    return stats


def safe_slug(title: str) -> str:
    title = re.sub(r'[/\\:*?"<>|\x00-\x1f]', '_', title).strip('. ')
    return title.encode('utf-8')[:170].decode('utf-8', errors='ignore') or 'article'


def write_post(stage: Path, rel: Path, title: str, topic: str, path: Path, body):
    timestamp = datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    content = body.decode_contents().replace('{%', '&#123;%').replace('{{', '&#123;{')
    front = f'---\ntitle: {json.dumps(title, ensure_ascii=False)}\ndate: {timestamp}\ncategories:\n  - 算法\n  - {topic}\n---\n\n'
    target = stage / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(front + '{% raw %}\n' + content + '\n{% endraw %}\n', encoding='utf-8')


def publish_stage(stage: Path, repo: Path, manifest: dict, manifest_path: Path = MANIFEST,
                  post_root: Path = POSTS, images_root: Path = IMAGES, baseline: dict | None = None):
    previous = json.loads((repo / manifest_path).read_text()) if (repo / manifest_path).exists() else {'files': baseline or {}}
    old, new = previous['files'], manifest['files']
    for name in set(old) | set(new):
        rel = Path(name)
        if '..' in rel.parts or rel.is_absolute() or not any(rel.is_relative_to(prefix) for prefix in (post_root, images_root)):
            raise ValueError('Invalid managed output path')
        target = repo / rel
        if target.is_symlink() or not target.resolve().is_relative_to(repo.resolve()):
            raise ValueError('Refusing to overwrite a symlink or escaped path')
        if target.exists() and (name not in old or digest(target.read_bytes()) != old[name]):
            raise ValueError(f'Refusing to overwrite an unmanaged or edited file: {name}')
    for name in new:
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((stage / name).read_bytes())
    for name in set(old) - set(new):
        (repo / name).unlink(missing_ok=True)
    (repo / manifest_path).parent.mkdir(parents=True, exist_ok=True)
    (repo / manifest_path).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run(source: Path, repo: Path, dry_run: bool = False) -> dict:
    source = source.expanduser().resolve()
    files = source_files(source)
    scrub = Scrubber(files)
    report = {'sources': len(files), 'articles': [], 'skipped': [], 'topics': {}, 'images': {}, 'files': {}}
    stats, topics = Counter(), Counter()
    with tempfile.TemporaryDirectory(prefix='logbook-algorithm-') as temp:
        stage = Path(temp)
        for path in files:
            title = scrub.title(path)
            identity = digest(path.relative_to(source).as_posix().encode())[:10]
            result = extract(path, source)
            if not result:
                report['skipped'].append({'id': identity, 'title': title, 'reason': '本地导出中未找到正文；需补充原始文档或完整 HTML'})
                continue
            body, content_path = result
            for tag in list(body.select(DROP)):
                if tag.parent:
                    tag.decompose()
            original_chars = len(body.get_text(strip=True))
            article_images = copy_images(body, content_path, source, stage, site_root(repo), scrub)
            stats.update(article_images)
            clean_dom(body, scrub)
            topic = classify(title)
            rel = POSTS / topic / f'{safe_slug(title)}--{identity}.md'
            write_post(stage, rel, title, topic, path, body)
            topics[topic] += 1
            report['articles'].append({'id': identity, 'title': title, 'path': rel.as_posix(), 'source_chars': original_chars, 'output_chars': len(body.get_text(strip=True)), 'images': dict(article_images)})
        if not report['articles']:
            raise ValueError('No extractable articles; existing outputs left untouched')
        report['topics'] = dict(sorted(topics.items()))
        report['images'] = dict(stats)
        report['files'] = {p.relative_to(stage).as_posix(): digest(p.read_bytes()) for p in sorted(stage.rglob('*')) if p.is_file()}
        report['unique_images'] = sum(p.startswith(str(IMAGES) + '/') for p in report['files'])
        report['review_required'] = '图片内的公司水印、姓名及业务数据未作 OCR 审核；文本清理不代表已获公开发布授权。'
        if not dry_run:
            publish_stage(stage, repo, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.home() / 'Documents/算法')
    parser.add_argument('--repo', type=Path, default=REPO)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        report = run(args.source, args.repo.resolve(), args.dry_run)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Import failed: {exc}\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'files', 'articles'}}, ensure_ascii=False, indent=2))
    print(f'Imported articles: {len(report["articles"])}')


if __name__ == '__main__':
    main()

