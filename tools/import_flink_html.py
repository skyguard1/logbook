#!/usr/bin/env python3
"""Import ~/Documents/flink into the local knowledge base without publishing."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from import_algorithm_html import REPO, run as import_collection
from import_algorithm_platform_html import AlgorithmPlatformScrubber, prepare_body

POSTS = Path('source/_posts/flink')
IMAGES = Path('source/images/flink')
MANIFEST = Path('tools/flink-import-manifest.json')
TOPICS = (
    ('监控与故障排查', r'监控|问题定位|故障|排查|Grafana|Prometh'),
    ('SQL与查询优化', r'ClickHouse|SQL|查询优化'),
    ('实时数仓与工程实践', r'数仓|实时计算|工程实践'),
)


class FlinkScrubber(AlgorithmPlatformScrubber):
    def __call__(self, text):
        text = re.sub(r'【DataMore】|智慧零售研发K吧|腾讯云大数据及人工智能', '', text, flags=re.I)
        return super().__call__(text)

    def title(self, path):
        title = super().title(path)
        return 'Flink笔记' if title == '算法平台笔记' else title


def classify(title):
    return next((topic for topic, pattern in TOPICS if re.search(pattern, title, re.I)), '基础原理与入门')


def run(source: Path, repo: Path = REPO, dry_run: bool = False):
    return import_collection(source, repo, dry_run, post_root=POSTS, images_root=IMAGES,
                             manifest_path=MANIFEST, category_label='flink',
                             classify_title=classify, scrubber_class=FlinkScrubber,
                             prepare_body=prepare_body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.home() / 'Documents/flink')
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
