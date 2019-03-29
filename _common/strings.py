from typing import Collection


def remove_suffix(s: str, suffix: str, other_suffixes: Collection[str]=None):
    all_suffixes = [suffix]
    if other_suffixes:
        all_suffixes += other_suffixes
    all_suffixes.sort(key=len, reverse=True)
    for suffix_ in filter(lambda x: len(x) > 0, all_suffixes):
        if s.endswith(suffix_):
            return s[:-len(suffix_)]
    return s


