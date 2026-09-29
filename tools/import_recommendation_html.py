#!/usr/bin/env python3
"""Import ~/Documents/推荐算法 into the current knowledge base's 推荐算法 category."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from import_algorithm_html import REPO, Scrubber, run as import_collection

POSTS = Path('source/_posts/recommendation')
IMAGES = Path('source/images/recommendation')
MANIFEST = Path('tools/recommendation-import-manifest.json')
TOPICS = (
    ('图学习与社交推荐', r'GNN|PlatoGL|图算法|图模型|社交推荐'),
    ('跨域推荐与冷启动', r'跨域|跨领域|跨领|冷启动|多领域|多场景'),
    ('多任务与多目标优化', r'多任务|多目标|强化学习'),
    ('召回排序与匹配', r'召回|排序|混排|匹配|实时相关推荐'),
    ('多模态与用户画像', r'多模态|内容表示|画像'),
    ('训练平台与实时工程', r'训练|Flink|流处理|数仓|平台'),
)


class RecommendationScrubber(Scrubber):
    """Remove known organisation identifiers without erasing technical headings."""
    EXTRA = re.compile('|'.join(map(re.escape, (
        '安全大数据实验室', '社交网络运营部数据中心', '增长中台体系',
        '社交网络运营部', '微信事业群', '腾讯公司研发管理部',
        '微信视频号直播平台部', '内容平台部', '诺亚方舟实验室',
    ))), re.I)

    def __call__(self, text: str) -> str:
        return self.EXTRA.sub('', super().__call__(text))

    def title(self, path: Path) -> str:
        # Preserve conference/year and technical-series prefixes, e.g. 【CIKM'20】.
        # Drop only the known platform metadata at the end of exported filenames.
        title = path.stem
        platform_export = False
        for suffix in (' - KM平台', ' - 腾讯iWiki'):
            if title.endswith(suffix):
                title = title[:-len(suffix)]
                platform_export = True
        if platform_export and ' - ' in title:
            title = title.rsplit(' - ', 1)[0]
        title = self(title)
        title = re.sub(r'【\s*】|\[\s*\]', '', title)
        title = re.sub(r'\s+', ' ', title).strip(' -_：:')
        return title or '推荐算法笔记'


def classify(title: str) -> str:
    return next((topic for topic, pattern in TOPICS if re.search(pattern, title, re.I)), '推荐算法基础')


def run(source: Path, repo: Path = REPO, dry_run: bool = False) -> dict:
    return import_collection(source, repo, dry_run, post_root=POSTS, images_root=IMAGES,
                             manifest_path=MANIFEST, category_label='推荐算法',
                             classify_title=classify, scrubber_class=RecommendationScrubber)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.home() / 'Documents/推荐算法')
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

