__all__ = [
    'CodeGraph'
]

import json
import os

from abc import ABCMeta
from json import JSONDecodeError

from .exceptions import CCMError
from .utils import create_property


class CodeGraph(metaclass=ABCMeta):
    """
    Abstract base class defining basic properties and functionality of a code
    digraph, which is intended to serve as a template for bytecode digraphs
    and source code digraphs.
    """
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialisation.
        """
        try:
            props = get_json(os.path.join(STATIC_DATA_FP, 'code_graph.json'))
        except (IOError, JSONDecodeError, OSError) as e:
            raise CCMError(e)

        for attr, val in props.items():
            kwargs.setdefault(attr, val['default'])
            setattr(self, '_{}'.format(attr), kwargs[attr])
            try:
                assert getattr(self, '_{}'.format(attr)) is not None
            except AssertionError:
                if val['nonnull']:
                    raise CCMError('Code graph property "{}" ({}, {}) cannot be null in init call'.format(attr, val['py_dtype'], val['desc']))
            setattr(self.__class__, attr, create_property(attr, attr_prefix='_', writable=val['writable']))

    def __repr__(self) -> str:
        return '{}(code="{}", org="{}", desc="{}", creation_time="{}", archive_uri="{}", imdb_client={}, cloud_client={})'.format(
            self.__class__.__name__,
            self.src_id,
            self.org,
            self.desc,
            self.creation_time,
            self.archive_uri,
            self.imdb_client,
            self.cloud_client
        )