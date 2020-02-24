__all__ = [
    'CCMError',
    'CCMException'
]


class CCMException(Exception):
    pass


class CCMError(CCMException):
    pass