from typing import Optional, get_type_hints, ClassVar, get_origin
from pydantic import BaseModel, create_model

def make_optional(model_cls: type[BaseModel]) -> type[BaseModel]:
    """
    Decorator to create a new Pydantic model with all instance fields set as optional.
    Class variables (annotated with ClassVar) are excluded.
    """
    annotations = get_type_hints(model_cls, include_extras=True)
    optional_fields = {}
    for field_name, field_type in annotations.items():
        if get_origin(field_type) is ClassVar:
            continue  # Skip ClassVar fields
        optional_fields[field_name] = (Optional[field_type], None)
    new_model = create_model(
        model_cls.__name__ + 'Optional',
        __base__=model_cls,
        **optional_fields
    )
    return new_model