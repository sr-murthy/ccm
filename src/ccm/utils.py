__all__ = [
    'create_property',
    'get_json',
    'pairwise',
    'STATIC_DATA_FP'
]

import io
import json
import os

from itertools import (
    tee,
    zip_longest,
)
from json import JSONDecodeError
from typing import (
    Iterable,
    Iterator,
)

from .exceptions import CCMError


STATIC_DATA_FP = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')


def create_property(name: str, attr_prefix: str = '', writable: bool = False) -> property:
    """
    Property factory method adapted from an excerpt from the book
    'Fluent Python' by Luciano Ramalho, O'Reilly, 2015.

    https://learning.oreilly.com/library/view/Fluent+Python/9781491946237/ch19.html#lineitem_class_v2prop

    :param name: Name of the underlying attribute
    :type name: str

    :param attr_prefix: Prefix of the underlying attribute
    :type attr_prefix: str

    :param writable: Whether the property value can be modified
    :type writable: bool

    :return: The property
    :rtype: property
    """
    def getter(obj):
        return obj.__dict__.get('{}{}'.format(attr_prefix, name))

    if not writable:
        return property(getter)

    def setter(obj, value):
        obj.__dict__.update({'{}{}'.format(attr_prefix, name): value})

    return property(getter, setter)


def get_json(src_fp: str) -> dict:
    """
    Loads JSON from file.

    :param src_fp: Source JSON file path
    :type src_fp: str

    :return: Dictionary
    :rtype: dict
    """
    try:
        with io.open(src_fp, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, JSONDecodeError, OSError, TypeError) as e:
        raise


def pairwise(it: Iterable) -> Iterator:
    """
    Returns an iterator of consecutive pairs of a given iterable.

    :param it: The iterable
    :type it: Iterable

    :return: Iterator of consecutive pairs of the input iterable
    :rtype: Iterator
    """
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(it)
    next(b, None)
    
    return zip_longest(a, b)
