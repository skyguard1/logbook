#!/usr/bin/env python3
"""Import ~/Documents/推荐系统 into the current knowledge base, without publishing."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from import_algorithm_html import COMPANIES, REPO, run as import_collection
from import_recommendation_html import RecommendationScrubber

POSTS = Path('source/_posts/recommender-system')
IMAGES = Path('source/images/recommender-system')
MANIFEST = Path('tools/recommender-system-import-manifest.json')
TOPICS = (
    ('知识图谱与图学习', r'WeKB|图谱|KG-BERT|GNN|图神经|图模型'),
    ('特征工程', r'特征|AutoGroup'),
    ('召回与匹配', r'召回|匹配|DSSM|MIND'),
    ('排序与全链路优化', r'粗排|精排|重排|混排|全链路|预取|过滤'),
    ('系统架构与工程实践', r'SRE|云原生|运维|容器|可靠性'),
    ('大数据基础', r'大数据|论文'),
)


class RecommenderSystemScrubber(RecommendationScrubber):
    EXTRA_ORGS = re.compile('|'.join(map(re.escape, (
        '微信视频号团队', '微信事业群', '工程效能平台部', '视频推荐工程中心',
        '光子业务技术运营组', '网络平台部', 'IEG流量生态部', '流量生态部',
        '腾讯产品经理', 'FiT研发线', 'Venus机器学习平台', '视频技术团队',
        'PCG Kbang 知识分享平台', 'TencentKG', '互娱增值服务部', '增值服务部',
        '微信', '微视', '雅虎', '苹果公司', '英特尔', '推特',
    ))), re.I)
    ENGLISH_ORGS = re.compile(
        r'(?<![A-Za-z0-9_.])(?:' + '|'.join(map(re.escape,
            [name for name in COMPANIES if name.isascii()] +
            ['PayPal', 'Twitter', 'Yahoo', 'Apple', 'LinkedIn', 'IBM', 'Hortonworks']))
        + r')(?![A-Za-z0-9_.])', re.I)

    def __call__(self, text: str) -> str:
        # Remove long attribution phrases before the parent removes their prefixes.
        text = text.replace('PayPal高级工程总监：', '').replace('及微信中的落地', '及业务中的落地')
        text = self.EXTRA_ORGS.sub('', text)
        return self.ENGLISH_ORGS.sub('', super().__call__(text))

    def title(self, path: Path) -> str:
        title = super().title(path)
        return '推荐系统笔记' if title == '推荐算法笔记' else title


def classify(title: str) -> str:
    return next((topic for topic, pattern in TOPICS if re.search(pattern, title, re.I)), '推荐系统基础与架构')


def run(source: Path, repo: Path = REPO, dry_run: bool = False) -> dict:
    return import_collection(source, repo, dry_run, post_root=POSTS, images_root=IMAGES,
                             manifest_path=MANIFEST, category_label='推荐系统',
                             classify_title=classify, scrubber_class=RecommenderSystemScrubber)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.home() / 'Documents/推荐系统')
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
