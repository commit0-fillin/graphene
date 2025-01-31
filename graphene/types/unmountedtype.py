from ..utils.orderedtype import OrderedType

class UnmountedType(OrderedType):
    """
    This class acts a proxy for a Graphene Type, so it can be mounted
    dynamically as Field, InputField or Argument.

    Instead of writing:

    .. code:: python

        from graphene import ObjectType, Field, String

        class MyObjectType(ObjectType):
            my_field = Field(String, description='Description here')

    It lets you write:

    .. code:: python

        from graphene import ObjectType, String

        class MyObjectType(ObjectType):
            my_field = String(description='Description here')

    It is not used directly, but is inherited by other types and streamlines their use in
    different context:

    - Object Type
    - Scalar Type
    - Enum
    - Interface
    - Union

    An unmounted type will accept arguments based upon its context (ObjectType, Field or
    InputObjectType) and pass it on to the appropriate MountedType (Field, Argument or InputField).

    See each Mounted type reference for more information about valid parameters.
    """

    def __init__(self, *args, **kwargs):
        super(UnmountedType, self).__init__()
        self.args = args
        self.kwargs = kwargs

    def get_type(self):
        """
        This function is called when the UnmountedType instance
        is mounted (as a Field, InputField or Argument)
        """
        return self.__class__(*self.args, **self.kwargs)

    def Field(self):
        """
        Mount the UnmountedType as Field
        """
        from .field import Field
        return Field(self.get_type(), *self.args, **self.kwargs)

    def InputField(self):
        """
        Mount the UnmountedType as InputField
        """
        from .inputfield import InputField
        return InputField(self.get_type(), *self.args, **self.kwargs)

    def Argument(self):
        """
        Mount the UnmountedType as Argument
        """
        from .argument import Argument
        return Argument(self.get_type(), *self.args, **self.kwargs)

    def __eq__(self, other):
        return self is other or (isinstance(other, UnmountedType) and self.get_type() == other.get_type() and (self.args == other.args) and (self.kwargs == other.kwargs))
