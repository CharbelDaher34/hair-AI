import random
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, create_model, Field
from elasticsearch import Elasticsearch
from enum import Enum
import json
import time
from client import AgentClient

# Comprehensive type mapping
ES_TYPE_MAP = {
    "text": str,
    "keyword": str,
    "integer": int,
    "long": int,
    "short": int,
    "byte": int,
    "double": float,
    "float": float,
    "half_float": float,
    "scaled_float": float,
    "boolean": bool,
    "date": datetime,
    "object": Dict[str, Any],
    "nested": List[Any],
}

# Fields that should be ignored in the model
IGNORED_FIELD_TYPES = {"alias"}

EXAMPLE_VALUES = {
    str: "example_string",
    int: 123,
    float: 1.23,
    bool: True,
    datetime: "2024-01-01T00:00:00Z",
    dict: {"key": "value"},
    list: ["item1", "item2"],
    Any: "any_value",
}


def get_distinct_field_values(
    index_name: str,
    field_path: str,
    es_host: str = "",
    size: int = 1000,
) -> List[Any]:
    """
    Get distinct values for any field in an Elasticsearch index.
    Automatically handles regular fields, nested fields, and multi-fields.

    Args:
        index_name: Name of the index to query
        field_path: Full path to the field (e.g., "card_type.keyword", "transaction.receiver.name.keyword")
        es_host: Elasticsearch host URL
        size: Maximum number of distinct values to return (default: 1000)

    Returns:
        List of distinct values for the specified field
    """
    try:
        es_client = Elasticsearch(hosts=[es_host])

        # Check if field is nested by looking for nested path in mapping
        mappings = es_client.indices.get_mapping(index=index_name)
        index_mapping = (
            mappings.get(index_name, {}).get("mappings", {}).get("properties", {})
        )

        # Determine if we need nested aggregation
        field_parts = field_path.split(".")
        nested_path = None

        # Check if any part of the path is a nested field
        current_mapping = index_mapping
        current_path = []

        for part in field_parts:
            current_path.append(part)
            if part in current_mapping:
                field_props = current_mapping[part]
                if field_props.get("type") == "nested":
                    nested_path = ".".join(current_path)
                    break
                elif "properties" in field_props:
                    current_mapping = field_props["properties"]

        # Build query based on whether field is nested or not
        if nested_path:
            # Nested field query
            query = {
                "size": 0,
                "aggs": {
                    "nested_agg": {
                        "nested": {"path": nested_path},
                        "aggs": {
                            "distinct_values": {
                                "terms": {"field": field_path, "size": size}
                            }
                        },
                    }
                },
            }

            response = es_client.search(index=index_name, body=query)
            buckets = (
                response.get("aggregations", {})
                .get("nested_agg", {})
                .get("distinct_values", {})
                .get("buckets", [])
            )
        else:
            # Regular field query
            query = {
                "size": 0,
                "aggs": {
                    "distinct_values": {"terms": {"field": field_path, "size": size}}
                },
            }

            response = es_client.search(index=index_name, body=query)
            buckets = (
                response.get("aggregations", {})
                .get("distinct_values", {})
                .get("buckets", [])
            )

        # Extract distinct values
        distinct_values = [bucket["key"] for bucket in buckets]
        return distinct_values

    except Exception as e:
        print(f"Error getting distinct values for field '{field_path}': {e}")
        return []


def get_example_value(py_type):
    # Handle typing.Union, typing.List, etc.
    origin = getattr(py_type, "__origin__", None)
    if origin is Union:
        # Pick the first non-None type
        for arg in py_type.__args__:
            if arg is not type(None):
                return get_example_value(arg)
    elif origin is list or origin is List:
        return [get_example_value(py_type.__args__[0])]
    elif origin is dict or origin is Dict:
        return {"key": get_example_value(py_type.__args__[1])}
    elif isinstance(py_type, type) and issubclass(py_type, Enum):
        # Handle Enum types - return the first enum value
        enum_values = list(py_type)
        if enum_values:
            try:
                return enum_values[0].value
            except:
                return enum_values[0].value
        return "enum_value"
    elif isinstance(py_type, type):
        return EXAMPLE_VALUES.get(py_type, f"example_{py_type.__name__}")
    return "example_value"


def es_type_to_pydantic(
    es_mapping: Dict[str, Any],
    model_name: str = "ESModel",
    fields_to_ignore: List[str] = [],
    category_fields: List[str] = [],
    index_name: str = None,
    es_host: str = "",
    current_path: str = "",
) -> BaseModel:
    """
    Convert Elasticsearch mapping to a Pydantic model, handling nested structures recursively.
    Creates Enum fields for specified category fields using distinct values from ES.
    """
    fields: Dict[str, tuple] = {}

    for field_name, field_props in es_mapping.items():
        # Build the full field path for nested fields
        full_field_path = f"{current_path}.{field_name}" if current_path else field_name

        # Skip ignored field types
        if (
            field_props.get("type") in IGNORED_FIELD_TYPES
            or field_name in fields_to_ignore
        ):
            continue

        es_type = field_props.get("type")
        sub_props = field_props.get("properties")

        # Handle nested/object types with properties (recursive case)
        if sub_props:
            # Recursively create nested model
            nested_model_name = f"{model_name}_{field_name.capitalize()}"
            nested_model = es_type_to_pydantic(
                sub_props,
                nested_model_name,
                fields_to_ignore,
                category_fields,
                index_name,
                es_host,
                full_field_path,  # Pass the current path to nested calls
            )

            # Handle nested arrays vs objects
            if es_type == "nested":
                py_type = List[nested_model]
            else:
                # For object type or when no type is specified but properties exist
                py_type = nested_model

        # Check if this field is a category field that should be an Enum
        # Check both the field name and the full path
        elif (
            field_name in category_fields or full_field_path in category_fields
        ) and index_name:
            try:
                # Get distinct values for this field using the full path
                field_path = (
                    f"{full_field_path}.keyword"
                    if es_type == "text"
                    else full_field_path
                )
                distinct_values = get_distinct_field_values(
                    index_name, field_path, es_host
                )

                if distinct_values:
                    # Create enum class name
                    enum_class_name = f"{model_name}_{field_name.capitalize()}Enum"

                    # Create enum members dict - handle special characters in values
                    enum_members = {}
                    for i, value in enumerate(distinct_values):
                        # Create valid Python identifier for enum member
                        if isinstance(value, str):
                            # Replace special characters and spaces
                            member_name = (
                                value.replace(" ", "_")
                                .replace("-", "_")
                                .replace("'", "")
                                .replace(".", "_")
                            )
                            # Ensure it starts with letter or underscore
                            if not member_name[0].isalpha() and member_name[0] != "_":
                                member_name = f"_{member_name}"
                            # Remove any remaining invalid characters
                            member_name = "".join(
                                c for c in member_name if c.isalnum() or c == "_"
                            )
                            # Ensure it's not empty
                            if not member_name:
                                member_name = f"VALUE_{i}"
                        else:
                            member_name = f"VALUE_{i}"

                        enum_members[member_name.upper()] = value

                    # Create the Enum class
                    category_enum = Enum(enum_class_name, enum_members)
                    py_type = category_enum
                else:
                    # Fallback to string if no distinct values found
                    base_type = ES_TYPE_MAP.get(es_type, str)
                    py_type = base_type
            except Exception as e:
                print(f"Error creating enum for field '{full_field_path}': {e}")
                # Fallback to string type
                base_type = ES_TYPE_MAP.get(es_type, str)
                py_type = base_type

        # Handle fields that don't have properties but might have multi-fields
        elif "fields" in field_props:
            # Use the main field type, ignore sub-fields for now
            base_type = ES_TYPE_MAP.get(es_type, str)  # Default to str for text fields
            py_type = base_type

        # Handle primitive fields
        else:
            # Get base type or default to Any
            base_type = ES_TYPE_MAP.get(es_type, Any)
            py_type = base_type

        # All fields are optional with None default
        if isinstance(py_type, type) and issubclass(py_type, Enum):
            # Enum fields are optional with None default
            fields[field_name] = (Optional[py_type], Field(default=None))
        elif isinstance(py_type, type) and issubclass(py_type, BaseModel):
            # Nested model fields are required (non-optional)
            fields[field_name] = (py_type, Field(...))
        elif hasattr(py_type, "__origin__") and py_type.__origin__ is list:
            # Check if it's List[BaseModel] - nested model arrays are required
            args = getattr(py_type, "__args__", ())
            if args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
                # List of nested models are required (non-optional)
                fields[field_name] = (py_type, Field(...))
            else:
                # Other lists are optional with None default
                fields[field_name] = (Optional[py_type], Field(default=None))
        else:
            # Other fields are optional with None default
            fields[field_name] = (Optional[py_type], Field(default=None))

    # Create the model class using create_model
    model_class = create_model(model_name, **fields)  # type: ignore

    # Return the class itself
    return model_class


def get_index_mapping(es_client: Elasticsearch, index_name: str) -> Dict[str, Any]:
    """
    Extract properties from index mapping, handling different ES versions.
    """
    mappings = es_client.indices.get_mapping(index=index_name)
    index_mapping = mappings.get(index_name, {}).get("mappings", {})

    # Handle modern ES structure
    if "properties" in index_mapping:
        return index_mapping["properties"]

    # Handle older ES versions
    return index_mapping.get("properties", {})


def create_pydantic_model_from_es(
    index_name: str,
    es_host: str = "",
    model_name: Optional[str] = None,
    fields_to_ignore: List[str] = ["user_id"],
    category_fields: List[str] = [],
) -> BaseModel:
    """
    Generate Pydantic model from Elasticsearch index mapping.
    """
    es_client = Elasticsearch(hosts=[es_host])
    properties = get_index_mapping(es_client, index_name)
    print(json.dumps(properties, indent=2))
    model_name = model_name or f"ES_{index_name.capitalize()}"
    return es_type_to_pydantic(
        properties,
        model_name=model_name,
        fields_to_ignore=fields_to_ignore,
        category_fields=category_fields,
        index_name=index_name,
        es_host=es_host,
        current_path="",
    )


# Example usage:
model = create_pydantic_model_from_es(
    "user_transactions",
    category_fields=["card_kind", "card_type", "transaction.receiver.category_type"],
    fields_to_ignore=["user_id", "card_number"],
)


def populate_with_examples_recursive(model: BaseModel) -> dict:
    result = {}
    for name, field_info in model.model_fields.items():
        annotation = field_info.annotation

        # Handle Optional types by extracting the inner type
        origin = getattr(annotation, "__origin__", None)
        if origin is Union:
            # Get the first non-None type from Union (Optional creates Union[T, None])
            inner_types = [arg for arg in annotation.__args__ if arg is not type(None)]
            if inner_types:
                annotation = inner_types[0]

        # Check if it's a BaseModel subclass (nested model)
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            result[name] = populate_with_examples_recursive(annotation)
        else:
            result[name] = get_example_value(annotation)
    return result


# Example usage functions
def example_get_distinct_values():
    """Example usage of the distinct values function"""
    print("\n=== Getting Distinct Values Examples ===")

    # Get distinct card types
    card_types = get_distinct_field_values("user_transactions", "card_type.keyword")
    print(f"Distinct card types: {card_types}")

    card_kinds = get_distinct_field_values("user_transactions", "card_kind.keyword")
    print(f"Distinct card kinds: {card_kinds}")

    category_types = get_distinct_field_values(
        "user_transactions", "category_type.keyword"
    )
    print(f"Distinct category types: {category_types}")

    # Get distinct transaction types
    transaction_types = get_distinct_field_values(
        "user_transactions", "transaction.type.keyword"
    )
    print(f"Distinct transaction types: {transaction_types}")

    # Get distinct receiver names from nested field
    receiver_names = get_distinct_field_values(
        "user_transactions", "transaction.receiver.name.keyword"
    )
    print(f"Distinct receiver names: {receiver_names}")

    # Get distinct receiver category types from nested field
    receiver_categories = get_distinct_field_values(
        "user_transactions", "transaction.receiver.category_type.keyword"
    )
    print(f"Distinct receiver categories: {receiver_categories}")


# Uncomment the line below to run examples
# example_get_distinct_values()

from typing import get_args, get_origin, Union, List
from pydantic import BaseModel
from datetime import date, datetime
import inspect


def extract_model_info(model_class: type[BaseModel], prefix: str = ""):
    """
    Extract field information from a Pydantic model class.
    Flattens all fields into a single dictionary using dot notation for nested fields.

    Args:
        model_class: A Pydantic BaseModel class (not an instance)
        prefix: Prefix for nested field names (used internally for recursion)

    Returns:
        Dict containing flattened field information with types and enum values
    """
    info = {}

    # Use model_fields to get field information from Pydantic models
    for field_name, field_info in model_class.model_fields.items():
        field_type = field_info.annotation
        origin = get_origin(field_type)
        args = get_args(field_type)

        # Create the full field name with prefix
        full_field_name = f"{prefix}.{field_name}" if prefix else field_name

        # Handle Optional types (Union[T, None])
        if origin is Union:
            # Get the first non-None type from Union
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                field_type = non_none_types[0]
                origin = get_origin(field_type)
                args = get_args(field_type)

        # Handle Enum types
        if inspect.isclass(field_type) and issubclass(field_type, Enum):
            info[full_field_name] = {
                "type": "enum",
                "values": [e.value for e in field_type],
            }
        # Handle nested BaseModel types - recursively flatten them
        elif inspect.isclass(field_type) and issubclass(field_type, BaseModel):
            # Recursively extract nested fields and merge them
            nested_info = extract_model_info(field_type, full_field_name)
            info.update(nested_info)
        # Handle List types
        elif origin is list or origin is List:
            if args:
                list_item_type = args[0]
                if inspect.isclass(list_item_type) and issubclass(
                    list_item_type, BaseModel
                ):
                    # For arrays of objects, we'll flatten the object structure
                    # but indicate it's an array field
                    nested_info = extract_model_info(list_item_type, full_field_name)
                    # Mark each nested field as being part of an array
                    for nested_field, nested_field_info in nested_info.items():
                        nested_field_info["is_array_item"] = True
                    info.update(nested_info)
                elif inspect.isclass(list_item_type) and issubclass(
                    list_item_type, Enum
                ):
                    info[full_field_name] = {
                        "type": "array",
                        "item_type": "enum",
                        "values": [e.value for e in list_item_type],
                    }
                else:
                    info[full_field_name] = {
                        "type": "array",
                        "item_type": _get_simple_type_name(list_item_type),
                    }
            else:
                info[full_field_name] = {"type": "array", "item_type": "unknown"}
        # Handle basic types
        elif field_type == str:
            info[full_field_name] = {"type": "string"}
        elif field_type in (int, float):
            info[full_field_name] = {"type": "number"}
        elif field_type == bool:
            info[full_field_name] = {"type": "boolean"}
        elif field_type in (date, datetime):
            info[full_field_name] = {"type": "date"}
        else:
            info[full_field_name] = {"type": _get_simple_type_name(field_type)}

    return info


def _get_simple_type_name(field_type) -> str:
    """Helper function to get a simple string representation of a type."""
    if hasattr(field_type, "__name__"):
        return field_type.__name__
    elif hasattr(field_type, "_name"):
        return field_type._name
    else:
        return str(field_type)


model_info = extract_model_info(model)
system_prompt = f"""
Today is {datetime.now().strftime("%Y-%m-%d")}

You are an expert assistant that converts natural language queries into structured database filters. Your task is to analyze user queries and translate them into precise filter conditions.

## Available Schema Fields:
{json.dumps(model_info, indent=2)}

## Supported Operators:
- "<" (less than) - for numbers and dates
- ">" (greater than) - for numbers and dates  
- "isin" (is in list) - for checking if value is in a list of options
- "notin" (not in list) - for checking if value is NOT in a list of options
- "is" (equals) - for exact matches
- "different" (not equals) - for exclusions
- "between" - for range queries (not yet implemented)

## Chain of Thought Process:
When analyzing a query, follow these steps:

1. **Identify Time References**: Look for temporal keywords (last summer, yesterday, this month, etc.)
2. **Extract Entities**: Find specific values mentioned (amounts, names, categories, etc.)
3. **Determine Intent**: Understand what the user wants to filter or find
4. **Map to Schema**: Match identified concepts to available schema fields
5. **Choose Operators**: Select appropriate operators based on the query type
6. **Validate Values**: Ensure values match field types and enum constraints

## Examples:

### Example 1: Time-based Query
**Query**: "what did i spend my money last summer?"
**Chain of Thought**:
- Time reference: "last summer" → June-August of previous year
- Intent: Find spending/transactions in that period
- Schema mapping: Need date field for time filtering
- Operator: ">" and "<" for date range, or "between"
- Result: Filter by transaction date between 2023-06-01 and 2023-08-31

### Example 2: Category-based Query  
**Query**: "show me all my restaurant purchases"
**Chain of Thought**:
- Entity: "restaurant" 
- Intent: Filter by merchant category
- Schema mapping: Look for category/merchant type fields
- Operator: "is" or "isin" if multiple restaurant categories exist
- Result: Filter where category_type is "restaurant" or similar

### Example 3: Amount-based Query
**Query**: "transactions over $100"
**Chain of Thought**:
- Entity: "$100" → numeric value 100
- Intent: Filter by transaction amount
- Schema mapping: Find amount/value field
- Operator: ">" for greater than
- Result: Filter where amount > 100

### Example 4: Card-based Query
**Query**: "purchases made with my credit card but not debit card"
**Chain of Thought**:
- Entities: "credit card", "debit card"
- Intent: Include credit, exclude debit
- Schema mapping: card_type or card_kind field
- Operators: "is" for credit, "different" for excluding debit
- Result: Multiple filters - card_type is "credit" AND card_type different "debit"

### Example 5: Complex Query
**Query**: "expensive coffee purchases from Starbucks in the last 3 months"
**Chain of Thought**:
- Time: "last 3 months" → date range
- Amount: "expensive" → subjective, maybe > $5 for coffee
- Merchant: "Starbucks" → specific receiver name
- Category: "coffee" → might map to restaurant/cafe category
- Multiple filters needed with AND logic

## Important Guidelines:

1. **Date Handling**: Convert relative dates (last month, yesterday) to absolute ISO dates (YYYY-MM-DD)
2. **Enum Values**: Only use values that exist in the enum lists provided in the schema
3. **Multiple Filters**: Create separate filter objects for each condition - they will be combined with AND logic
4. **Ambiguous Queries**: When unclear, prefer broader filters rather than overly restrictive ones
5. **Missing Information**: If a query references data not available in the schema, explain what's missing

## Response Format:
Always return a valid JSON object matching the QueryFilters schema with a "filters" array containing Query objects.

Now, analyze the user's query and provide the appropriate filters:
"""
from enum import Enum
from typing import List, Union
from pydantic import BaseModel, field_validator, ValidationError
import json


# These operators will be supported in the LLM output
class OperatorEnum(str, Enum):
    lt = "<"
    gt = ">"
    isin = "isin"
    notin = "notin"
    eq = "is"
    ne = "different"
    be = "between"


def make_field_enum(model_info: dict):
    return Enum("FieldEnum", {k: k for k in model_info.keys()})


model_info = extract_model_info(model)
FieldEnum = make_field_enum(model_info)


class Query(BaseModel):
    field: FieldEnum
    operator: OperatorEnum
    value: Union[
        str, float, int, List[str], List[date]
    ]  # simplified to str and validated later

    @field_validator("value")
    def validate_value(cls, v, values):
        if "field" not in values or "operator" not in values:
            return v

        field = values["field"].value
        op = values["operator"].value
        info = model_info[field]
        ftype = info["type"]

        def fail(msg):
            raise ValueError(
                f"Invalid value for field '{field}' with type '{ftype}': {msg}"
            )

        if op in ("<", ">"):
            if ftype not in ("number", "date"):
                fail(f"Operator '{op}' only valid for number/date fields")
            if ftype == "number":
                try:
                    float(v)
                except:
                    fail("Expected numeric value")
            elif ftype == "date":
                try:
                    from datetime import date

                    if isinstance(v, str):
                        date.fromisoformat(v)
                except:
                    fail("Expected ISO date string (YYYY-MM-DD)")

        elif op in ("isin", "notin"):
            if not isinstance(v, list):
                fail("Expected list of values")
            if ftype == "enum":
                allowed = info.get("values", [])
                if not all(x in allowed for x in v):
                    fail(f"Values must be in enum: {allowed}")

        elif op in ("is", "different"):
            if ftype == "enum":
                if v not in info.get("values", []):
                    fail(f"Must be one of {info.get('values', [])}")
            elif ftype == "number":
                try:
                    float(v)
                except:
                    fail("Expected number")
            elif ftype == "boolean":
                if v not in [True, False, "true", "false", "True", "False"]:
                    fail("Expected boolean")
            elif ftype == "date":
                try:
                    from datetime import date

                    date.fromisoformat(v)
                except:
                    fail("Expected date in ISO format")
        return v


class QueryFilters(BaseModel):
    filters: List[Query]


print(system_prompt)
client = AgentClient(
    system_prompt=system_prompt,
    schema=QueryFilters.model_json_schema(),
    inputs=[
        "what did i spend my money last summer? give me the amount spent on trips, expensive items, and using my gold credit card"
    ],
)
print(json.dumps(client.parse(), indent=2))

client = AgentClient(
    system_prompt=system_prompt,
    schema=QueryFilters.model_json_schema(),
    inputs=[
        "what did i spend my money last summer?, focus on tech and food expensive transactions"
    ],
)
print(json.dumps(client.parse(), indent=2))
