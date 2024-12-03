from graphql import GraphQLError
from graphql.language import FieldNode
from graphql.validation import ValidationRule
from ..utils.is_introspection_key import is_introspection_key

class DisableIntrospection(ValidationRule):
    def enter_field(self, node: FieldNode, *args):
        field_name = node.name.value

        if is_introspection_key(field_name):
            raise GraphQLError(
                f"GraphQL introspection is not allowed, but the query contained {field_name}.",
                [node]
            )
