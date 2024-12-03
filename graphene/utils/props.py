class _OldClass:
    pass

class _NewClass:
    pass
_all_vars = set(dir(_OldClass) + dir(_NewClass))

def props(x):
    """
    Returns all the properties of an object, excluding the ones from built-in classes.
    """
    return {
        key: getattr(x, key)
        for key in set(dir(x)) - _all_vars
        if not key.startswith("_")
    }

def get_class_name(obj):
    """
    Returns the class name of an object.
    """
    return obj.__class__.__name__

def has_attribute(obj, attr_name):
    """
    Checks if an object has a specific attribute.
    """
    return hasattr(obj, attr_name)

def get_methods(obj):
    """
    Returns all methods of an object.
    """
    return [method for method in dir(obj) if callable(getattr(obj, method)) and not method.startswith("__")]
