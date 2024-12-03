import inspect
from functools import partial
from ..utils.module_loading import import_string
from .mountedtype import MountedType
from .unmountedtype import UnmountedType

def get_field_as(value, _as=None):
    """
    Get type mounted
    """
    if isinstance(value, MountedType):
        return value
    elif isinstance(value, UnmountedType):
        return value.mount(_as)
    return _as(value) if _as else value

def yank_fields_from_attrs(attrs, _as=None, sort=True):
    """
    Extract all the fields in given attributes (dict)
    and return them ordered
    """
    fields = {}
    for key, value in attrs.items():
        if isinstance(value, (MountedType, UnmountedType)):
            fields[key] = get_field_as(value, _as)
    
    if sort:
        fields = dict(sorted(fields.items(), key=lambda f: f[1]))
    
    return fields

def get_underlying_type(_type):
    """Get the underlying type even if it is wrapped in structures like NonNull"""
    while hasattr(_type, 'of_type'):
        _type = _type.of_type
    return _type
