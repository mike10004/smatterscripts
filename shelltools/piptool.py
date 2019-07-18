#!/usr/bin/python3

import json
import logging
import requests
from typing import Any, List


_log = logging.getLogger(__name__)


def fetch_definition(package: str, version: str=None):
    package = package.strip()
    if not package:
        raise ValueError("package name must be non-empty and non-whitespace")
    url_parts = ['https://pypi.org/pypi', package]
    if version is not None:
        url_parts.append(version)
    url = '/'.join(url_parts + ['json'])
    definition = requests.get(url).json()
    return definition


def format_output(output: Any) -> List:
    _log.debug("output has type %s", type(output))
    if isinstance(output, dict):
        return [json.dumps(output, indent=2)]
    if isinstance(output, list):
        return output
    _log.info("unrecognized content type in output: %s", type(output))
    return [output]


def main(args=None):
    transforms = {
        'none': lambda x: x,
        'info': lambda d: d['info'],
        'deps': lambda d: d['info']['requires_dist']
    }

    from argparse import ArgumentParser
    parser = ArgumentParser(description="""\
Fetches a package definition from PyPI and prints it. The original motivation \
was a need to print the dependencies of a package, and this functionality is \
available with --transform=deps. 
""")
    parser.add_argument("package", help="package name")
    parser.add_argument("--version", help="specify package version")
    parser.add_argument("--transform", choices=transforms.keys(), metavar="MODE", default='none', help="transform output; choose from " + str(set(transforms.keys())))
    parser.add_argument("-l", "--log-level", choices=('DEBUG', 'INFO', 'WARN', 'ERROR'), default='INFO', help="set log level")
    args = parser.parse_args(args)
    logging.basicConfig(level=logging.__dict__[args.log_level])
    definition = fetch_definition(args.package, args.version)
    transform = transforms[args.transform]
    output = transform(definition)
    output = format_output(output)
    assert isinstance(output, list)
    for item in output:
        print(item)
    return 0
