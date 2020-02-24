__all__ = [
    'pairwise'
]


from itertools import (
    tee,
    zip_longest,
)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    
    return zip_longest(a, b)