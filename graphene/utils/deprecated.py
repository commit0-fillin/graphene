import functools
import inspect
import warnings
string_types = (type(b''), type(''))

def deprecated(reason):
    """
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.
    """
    def decorator(func):
        if isinstance(func, string_types):
            fmt = "{0} is deprecated. {1}"
            msg = fmt.format(func, reason)
            raise TypeError(msg)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated. {reason}",
                category=DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)

        return wrapper

    if isinstance(reason, string_types):
        return decorator
    else:
        return decorator(reason)
