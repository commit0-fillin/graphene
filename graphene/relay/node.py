from functools import partial
from inspect import isclass
from ..types import Field, Interface, ObjectType
from ..types.interface import InterfaceOptions
from ..types.utils import get_type
from .id_type import BaseGlobalIDType, DefaultGlobalIDType

def is_node(objecttype):
    """
    Check if the given objecttype has Node as an interface
    """
    return Node in objecttype._meta.interfaces

class GlobalID(Field):

    def __init__(self, node=None, parent_type=None, required=True, global_id_type=DefaultGlobalIDType, *args, **kwargs):
        super(GlobalID, self).__init__(global_id_type.graphene_type, *args, required=required, **kwargs)
        self.node = node or Node
        self.parent_type_name = parent_type._meta.name if parent_type else None

class NodeField(Field):

    def __init__(self, node, type_=False, **kwargs):
        assert issubclass(node, Node), 'NodeField can only operate in Nodes'
        self.node_type = node
        self.field_type = type_
        global_id_type = node._meta.global_id_type
        super(NodeField, self).__init__(type_ or node, id=global_id_type.graphene_type(required=True, description='The ID of the object'), **kwargs)

class AbstractNode(Interface):

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, global_id_type=DefaultGlobalIDType, **options):
        assert issubclass(global_id_type, BaseGlobalIDType), 'Custom ID type need to be implemented as a subclass of BaseGlobalIDType.'
        _meta = InterfaceOptions(cls)
        _meta.global_id_type = global_id_type
        _meta.fields = {'id': GlobalID(cls, global_id_type=global_id_type, description='The ID of the object')}
        super(AbstractNode, cls).__init_subclass_with_meta__(_meta=_meta, **options)

class Node(AbstractNode):
    """An object with an ID"""
