#!/usr/bin/env python3

"""Module that provides utilities for working with predicates."""

from typing import Callable


# noinspection PyUnusedLocal
def _ALWAYS_FALSE(*args, **kwargs):
    return False

# noinspection PyUnusedLocal
def _ALWAYS_TRUE(*args, **kwargs):
    return True


def _NOT_NONE(x):
    return x is not None


def always_true() -> Callable:
    return _ALWAYS_TRUE


def always_false() -> Callable:
    return _ALWAYS_FALSE


def And(*args):
    def g(*args_, **kwargs_):
        for f in args:
            if not f(*args_, **kwargs_):
                return False
        return True
    return g


def not_none():
    return _NOT_NONE
