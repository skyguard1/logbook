#!/usr/bin/env python3
"""Validate Flink titles, redaction, image paths and optional browser layout."""
import argparse
from pathlib import Path

from import_flink_html import FlinkScrubber, IMAGES, MANIFEST
from validate_recommender_system_import import validate


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', help='Local Hexo origin, e.g. http://127.0.0.1:4017')
    parser.add_argument('--source', type=Path, default=Path.home() / 'Documents/flink')
    args = parser.parse_args()
    validate(args.origin, manifest=MANIFEST, images=IMAGES, category='flink',
             scrubber_class=FlinkScrubber, source=args.source.expanduser())
