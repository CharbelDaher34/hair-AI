from typing import Optional, get_type_hints, ClassVar, get_origin, List
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



from typing import Any
from pydantic import BaseModel

from typing import Any
from pydantic import BaseModel

def render_model(model: Any, indent: int = 0) -> str:
    spacer = "  " * indent

    def format_entry(key: str, value: Any, level: int) -> str:
        prefix = "  " * level + f"{key}:"

        if isinstance(value, BaseModel) or isinstance(value, dict):
            return f"{prefix}\n" + render_model(value, level + 1)

        elif isinstance(value, list):
            if not value:
                return f"{prefix} []"
            entries = []
            for idx, item in enumerate(value, 1):
                if isinstance(item, BaseModel) or isinstance(item, dict):
                    item_str = render_model(item, level + 2)
                    entries.append(f"{'  ' * (level + 1)}{idx}.\n{item_str}")
                else:
                    entries.append(f"{'  ' * (level + 1)}{idx}. {item}")
            return f"{prefix}\n" + "\n".join(entries)

        else:
            return f"{prefix} {value}"

    lines = []
    if isinstance(model, BaseModel):
        data = model.__dict__
    elif isinstance(model, dict):
        data = model
    else:
        raise TypeError(f"Expected BaseModel or dict, got {type(model)}")

    for field_name, value in data.items():
        if value is not None:
            lines.append(format_entry(field_name, value, indent))

    return "\n".join(lines)

