from enum import Enum as PyEnum
import inspect
from functools import partial
from graphql import default_type_resolver, get_introspection_query, graphql, graphql_sync, introspection_types, parse, print_schema, subscribe, validate, ExecutionResult, GraphQLArgument, GraphQLBoolean, GraphQLError, GraphQLEnumValue, GraphQLField, GraphQLFloat, GraphQLID, GraphQLInputField, GraphQLInt, GraphQLList, GraphQLNonNull, GraphQLObjectType, GraphQLSchema, GraphQLString
from ..utils.str_converters import to_camel_case
from ..utils.get_unbound_function import get_unbound_function
from .definitions import GrapheneEnumType, GrapheneGraphQLType, GrapheneInputObjectType, GrapheneInterfaceType, GrapheneObjectType, GrapheneScalarType, GrapheneUnionType
from .dynamic import Dynamic
from .enum import Enum
from .field import Field
from .inputobjecttype import InputObjectType
from .interface import Interface
from .objecttype import ObjectType
from .resolver import get_default_resolver
from .scalars import ID, Boolean, Float, Int, Scalar, String
from .structures import List, NonNull
from .union import Union
from .utils import get_field_as
introspection_query = get_introspection_query()
IntrospectionSchema = introspection_types['__Schema']

class TypeMap(dict):

    def __init__(self, query=None, mutation=None, subscription=None, types=None, auto_camelcase=True):
        assert_valid_root_type(query)
        assert_valid_root_type(mutation)
        assert_valid_root_type(subscription)
        if types is None:
            types = []
        for type_ in types:
            assert is_graphene_type(type_)
        self.auto_camelcase = auto_camelcase
        create_graphql_type = self.add_type
        self.query = create_graphql_type(query) if query else None
        self.mutation = create_graphql_type(mutation) if mutation else None
        self.subscription = create_graphql_type(subscription) if subscription else None
        self.types = [create_graphql_type(graphene_type) for graphene_type in types]

    def get_function_for_type(self, graphene_type, func_name, name, default_value):
        """Gets a resolve or subscribe function for a given ObjectType"""
        if isinstance(graphene_type, GrapheneGraphQLType):
            graphene_type = graphene_type.graphene_type
        
        if isinstance(graphene_type, type) and issubclass(graphene_type, ObjectType):
            func = getattr(graphene_type, func_name, None)
            if func:
                return func
        
        return default_value

class Schema:
    """Schema Definition.
    A Graphene Schema can execute operations (query, mutation, subscription) against the defined
    types. For advanced purposes, the schema can be used to lookup type definitions and answer
    questions about the types through introspection.
    Args:
        query (Type[ObjectType]): Root query *ObjectType*. Describes entry point for fields to *read*
            data in your Schema.
        mutation (Optional[Type[ObjectType]]): Root mutation *ObjectType*. Describes entry point for
            fields to *create, update or delete* data in your API.
        subscription (Optional[Type[ObjectType]]): Root subscription *ObjectType*. Describes entry point
            for fields to receive continuous updates.
        types (Optional[List[Type[ObjectType]]]): List of any types to include in schema that
            may not be introspected through root types.
        directives (List[GraphQLDirective], optional): List of custom directives to include in the
            GraphQL schema. Defaults to only include directives defined by GraphQL spec (@include
            and @skip) [GraphQLIncludeDirective, GraphQLSkipDirective].
        auto_camelcase (bool): Fieldnames will be transformed in Schema's TypeMap from snake_case
            to camelCase (preferred by GraphQL standard). Default True.
    """

    def __init__(self, query=None, mutation=None, subscription=None, types=None, directives=None, auto_camelcase=True):
        self.query = query
        self.mutation = mutation
        self.subscription = subscription
        type_map = TypeMap(query, mutation, subscription, types, auto_camelcase=auto_camelcase)
        self.graphql_schema = GraphQLSchema(type_map.query, type_map.mutation, type_map.subscription, type_map.types, directives)

    def __str__(self):
        return print_schema(self.graphql_schema)

    def __getattr__(self, type_name):
        """
        This function let the developer select a type in a given schema
        by accessing its attrs.
        Example: using schema.Query for accessing the "Query" type in the Schema
        """
        _type = self.graphql_schema.get_type(type_name)
        if _type is None:
            raise AttributeError(f'Type "{type_name}" not found in the Schema')
        if isinstance(_type, GrapheneGraphQLType):
            return _type.graphene_type
        return _type

    def execute(self, *args, **kwargs):
        """Execute a GraphQL query on the schema.
        Use the `graphql_sync` function from `graphql-core` to provide the result
        for a query string. Most of the time this method will be called by one of the Graphene
        :ref:`Integrations` via a web request.
        Args:
            request_string (str or Document): GraphQL request (query, mutation or subscription)
                as string or parsed AST form from `graphql-core`.
            root_value (Any, optional): Value to use as the parent value object when resolving
                root types.
            context_value (Any, optional): Value to be made available to all resolvers via
                `info.context`. Can be used to share authorization, dataloaders or other
                information needed to resolve an operation.
            variable_values (dict, optional): If variables are used in the request string, they can
                be provided in dictionary form mapping the variable name to the variable value.
            operation_name (str, optional): If multiple operations are provided in the
                request_string, an operation name must be provided for the result to be provided.
            middleware (List[SupportsGraphQLMiddleware]): Supply request level middleware as
                defined in `graphql-core`.
            execution_context_class (ExecutionContext, optional): The execution context class
                to use when resolving queries and mutations.
        Returns:
            :obj:`ExecutionResult` containing any data and errors for the operation.
        """
        return graphql_sync(self.graphql_schema, *args, **kwargs)

    async def execute_async(self, *args, **kwargs):
        """Execute a GraphQL query on the schema asynchronously.
        Same as `execute`, but uses `graphql` instead of `graphql_sync`.
        """
        return await graphql(self.graphql_schema, *args, **kwargs)

    async def subscribe(self, query, *args, **kwargs):
        """Execute a GraphQL subscription on the schema asynchronously."""
        document = parse(query)
        return await subscribe(self.graphql_schema, document, *args, **kwargs)

def normalize_execute_kwargs(kwargs):
    """Replace alias names in keyword arguments for graphql()"""
    for old, new in [
        ("context", "context_value"),
        ("root", "root_value"),
        ("variables", "variable_values"),
    ]:
        if old in kwargs:
            kwargs[new] = kwargs.pop(old)
    return kwargs
