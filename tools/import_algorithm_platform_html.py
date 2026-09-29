#!/usr/bin/env python3
"""Import local 算法平台 HTML into this knowledge base without publishing."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup
from import_algorithm_html import DEPARTMENTS, INTERNAL, REPO, local_file, run as import_collection
from import_recommender_system_html import RecommenderSystemScrubber

POSTS = Path('source/_posts/algorithm-platform')
IMAGES = Path('source/images/algorithm-platform')
MANIFEST = Path('tools/algorithm-platform-import-manifest.json')
TOPICS = (
    ('实验评估与指标', r'ABtest|A/B|CUPED|评价指标|评估|多样性分析'),
    ('图学习与图计算', r'Graph|GNN|Plato|Embedx2|图卷积|图神经|图计算|图表示|图排序|图召回'),
    ('多模态与内容理解', r'多模态|视频分类|标签|内容理解|知识图谱|KBQA|SG-ZSVC|MMCN|TMCL|LDA|标注'),
    ('特征工程与用户建模', r'特征|画像|user embedding|Bert4User|PeterRec|全行为序列'),
    ('召回与向量检索', r'召回|Faiss|相似性|匹配|Look.alike|LookAlike'),
    ('排序与预估模型', r'排序|粗排|精排|CTR|CVR|FFM|DeepFM|多目标|多任务|点击率|预估|模型'),
    ('训练与工程优化', r'预训练|训练|word2vec|Fasttext|性能|Pyspark|embedding|BERT'),
)
ORG_PHRASES = (
    '腾讯微创新奖', '腾讯知文', '博通技术干货', '博通内容理解团队', '博通团队',
    '信息安全部-技术研发中心', '信息安全部', '技术研发中心',
    '广告多媒体AI中心团队', '创意中心-创意产品组团队', '创意中心-创意产品组',
    '全民K歌商业化团队', '微视短视频推荐算法团队', '微视推荐工程团队',
    '微信支付研发团队', '微信后台开发', 'AI Lab&Robotics X-内部交流吧',
    'AI平台部&AI Lab&Robotics X-内部交流吧', '优图实验室', 'Tencent YouTu Lab',
    '腾讯看点数据中心', '腾讯看点商业化开发', '腾讯数据科学',
    '腾讯音乐 智能数据中心', '桌面安全产品部后台开发组', '信息流平台产品部',
    'SPA 社交与效果广告部', '社交与效果广告部', '搜索内容技术组',
    'IEG游戏直播业务部', '游戏直播业务部', 'SNG社交网络运营部数据中心',
    '信息平台与服务线 IPS View', 'TKD技术学院', '腾讯技术周',
    'CROS FAMILY（公共研发运营体系）', 'PCGtime', 'OMG T族职级晋升分享吧',
    'TEG 技术之眼', '看点推荐小牛', '腾讯罗盘', '腾讯网财富库', '腾讯大讲堂',
    '腾讯大数据', '腾讯云小微', '腾讯产品经理', '内平内容算法圈', '信息流内容理解',
)


class AlgorithmPlatformScrubber(RecommenderSystemScrubber):
    EXTRA_PLATFORM_ORGS = re.compile('|'.join(map(re.escape, sorted(ORG_PHRASES, key=len, reverse=True))), re.I)

    def __init__(self, files):
        # Only learn final export metadata, not technical subtitles separated by " - ".
        self.metadata = set(DEPARTMENTS) | set(ORG_PHRASES)
        for path in files:
            stem = self.strip_platform(path.stem)
            if stem != path.stem and ' - ' in stem:
                self.metadata.add(stem.rsplit(' - ', 1)[1])
        super().__init__([Path('article - ' + suffix + '.html') for suffix in sorted(self.metadata)])

    @staticmethod
    def strip_platform(title):
        for suffix in (' - KM平台', ' - 腾讯iWiki'):
            if title.endswith(suffix):
                return title[:-len(suffix)]
        return title

    def __call__(self, text):
        text = re.sub(r'【腾讯微创新奖\d*期】|【腾讯知文】|【博通技术干货】|【AI\s*LAB】', '', text, flags=re.I)
        text = re.sub(r'(?:[A-Za-z0-9-]+\.)*(?:woa|oa)\.com\b[^\s<>"\'，。；（）)]*', '[内部链接已移除]', text, flags=re.I)
        return super().__call__(self.EXTRA_PLATFORM_ORGS.sub('', text))

    def title(self, path):
        title = self.strip_platform(path.stem)
        while ' - ' in title and title.rsplit(' - ', 1)[1] in self.metadata:
            title = title.rsplit(' - ', 1)[0]
        title = re.sub(r'【\s*】|\[\s*\]|（\s*）|\(\s*\)', '', self(title))
        return re.sub(r'\s+', ' ', title).strip(' -_：:') or '算法平台笔记'


def classify(title):
    return next((topic for topic, pattern in TOPICS if re.search(pattern, title, re.I)), '平台架构与系统设计')


def prepare_body(body, content_path, source):
    for macro in list(body.select('[data-macro-name="md"], [data-macro-name="cherry"]')):
        frame = macro.select_one('iframe[src]')
        preview = local_file(frame['src'], content_path, source) if frame else None
        rendered = None
        if preview:
            soup = BeautifulSoup(preview.read_bytes(), 'html.parser')
            rendered = soup.select_one('.cherry-markdown, .markdown-body')
        if rendered is None or not (rendered.get_text(strip=True) or rendered.find('img')):
            raise ValueError(f'Missing rendered Markdown preview: {content_path.name}')
        for img in rendered.find_all('img'):
            for key in ('src', 'data-src', 'data-original'):
                if key in img.attrs:
                    resource = local_file(str(img[key]), preview, source)
                    if resource:
                        img[key] = os.path.relpath(resource, content_path.parent)
        macro.replace_with(rendered)
    for tag in list(body.select('.md-loading, .cherry-loading, .md-code-placeholder, .cherry-placeholder, .tf-inline-btn-container, .tf-inline-filter, .handy-header')):
        if tag.parent:
            tag.decompose()
    for link in body.find_all('a', href=True):
        url = str(link['href'])
        if INTERNAL.search(url):
            link['href'] = ''  # The shared cleaner will unwrap it, preserving reference text.
        elif re.match(r'https://github\.com/Tencent/', url, re.I) and link.get_text(strip=True).startswith('http'):
            link.clear()
            link.append('开源项目：' + url.rstrip('/').rsplit('/', 1)[-1])


def run(source: Path, repo: Path = REPO, dry_run: bool = False):
    return import_collection(source, repo, dry_run, post_root=POSTS, images_root=IMAGES,
                             manifest_path=MANIFEST, category_label='算法平台',
                             classify_title=classify, scrubber_class=AlgorithmPlatformScrubber,
                             prepare_body=prepare_body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.home() / 'Documents/算法平台')
    parser.add_argument('--repo', type=Path, default=REPO)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        report = run(args.source, args.repo.resolve(), args.dry_run)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Import failed: {exc}\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'articles', 'files'}}, ensure_ascii=False, indent=2))
    print('Imported articles:', len(report['articles']))


if __name__ == '__main__':
    main()
