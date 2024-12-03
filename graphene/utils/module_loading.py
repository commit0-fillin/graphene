from functools import partial
from importlib import import_module

def import_string(dotted_path, dotted_attributes=None):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. When a dotted attribute path is also provided, the
    dotted attribute path would be applied to the attribute/class retrieved from
    the first step, and return the corresponding value designated by the
    attribute path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    try:
        module = import_module(module_path)
    except ImportError as err:
        raise ImportError('Module "%s" does not exist' % module_path) from err

    try:
        attr = getattr(module, class_name)
    except AttributeError as err:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (module_path, class_name)) from err

    if dotted_attributes:
        for attribute in dotted_attributes.split('.'):
            try:
                attr = getattr(attr, attribute)
            except AttributeError as err:
                raise ImportError('Attribute "%s" not found in "%s"' % (attribute, attr)) from err

    return attr
