import re
from collections.abc import Iterable
from functools import partial
from typing import Type
from graphql_relay import connection_from_array
from ..types import Boolean, Enum, Int, Interface, List, NonNull, Scalar, String, Union
from ..types.field import Field
from ..types.objecttype import ObjectType, ObjectTypeOptions
from ..utils.thenables import maybe_thenable
from .node import is_node, AbstractNode

class PageInfo(ObjectType):

    class Meta:
        description = 'The Relay compliant `PageInfo` type, containing data necessary to paginate this connection.'
    has_next_page = Boolean(required=True, name='hasNextPage', description='When paginating forwards, are there more items?')
    has_previous_page = Boolean(required=True, name='hasPreviousPage', description='When paginating backwards, are there more items?')
    start_cursor = String(name='startCursor', description='When paginating backwards, the cursor to continue.')
    end_cursor = String(name='endCursor', description='When paginating forwards, the cursor to continue.')

def page_info_adapter(startCursor, endCursor, hasPreviousPage, hasNextPage):
    """Adapter for creating PageInfo instances"""
    return PageInfo(
        start_cursor=startCursor,
        end_cursor=endCursor,
        has_previous_page=hasPreviousPage,
        has_next_page=hasNextPage
    )

class ConnectionOptions(ObjectTypeOptions):
    node = None

class Connection(ObjectType):

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, node=None, name=None, strict_types=False, _meta=None, **options):
        if not _meta:
            _meta = ConnectionOptions(cls)
        assert node, f'You have to provide a node in {cls.__name__}.Meta'
        assert isinstance(node, NonNull) or issubclass(node, (Scalar, Enum, ObjectType, Interface, Union, NonNull)), f'Received incompatible node "{node}" for Connection {cls.__name__}.'
        base_name = re.sub('Connection$', '', name or cls.__name__) or node._meta.name
        if not name:
            name = f'{base_name}Connection'
        options['name'] = name
        _meta.node = node
        if not _meta.fields:
            _meta.fields = {}
        if 'page_info' not in _meta.fields:
            _meta.fields['page_info'] = Field(PageInfo, name='pageInfo', required=True, description='Pagination data for this connection.')
        if 'edges' not in _meta.fields:
            edge_class = get_edge_class(cls, node, base_name, strict_types)
            cls.Edge = edge_class
            _meta.fields['edges'] = Field(NonNull(List(NonNull(edge_class) if strict_types else edge_class)), description='Contains the nodes in this connection.')
        return super(Connection, cls).__init_subclass_with_meta__(_meta=_meta, **options)

def connection_adapter(cls, edges, pageInfo):
    """Adapter for creating Connection instances"""
    return cls(
        edges=edges,
        page_info=page_info_adapter(
            startCursor=pageInfo.get('startCursor'),
            endCursor=pageInfo.get('endCursor'),
            hasPreviousPage=pageInfo.get('hasPreviousPage'),
            hasNextPage=pageInfo.get('hasNextPage')
        )
    )

class IterableConnectionField(Field):

    def __init__(self, type_, *args, **kwargs):
        kwargs.setdefault('before', String())
        kwargs.setdefault('after', String())
        kwargs.setdefault('first', Int())
        kwargs.setdefault('last', Int())
        super(IterableConnectionField, self).__init__(type_, *args, **kwargs)
ConnectionField = IterableConnectionField
