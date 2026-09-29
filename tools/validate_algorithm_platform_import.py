#!/usr/bin/env python3
"""Validate algorithm-platform imports, built assets and optional browser layout."""
import argparse

from import_algorithm_platform_html import MANIFEST, IMAGES, AlgorithmPlatformScrubber
from validate_recommender_system_import import validate as validate_collection


def validate(origin=None):
    return validate_collection(origin, manifest=MANIFEST, images=IMAGES,
                               category='算法平台', scrubber_class=AlgorithmPlatformScrubber)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', help='Optional local Hexo origin, e.g. http://127.0.0.1:4017')
    validate(parser.parse_args().origin)
