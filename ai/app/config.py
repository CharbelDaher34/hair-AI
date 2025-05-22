from pydantic import BaseModel, Field, create_model
from typing import Optional, List, Dict, Any, Type, Union
from enum import Enum

from typing import Any, Optional

from pydantic import BaseModel, Field, create_model
from utils import create_model_from_schema

class ModelType(str, Enum):
    LLM = "llm"
    LLM_CHAT = "llm_chat"
    LLM_CHAT_STREAM = "llm_chat_stream"
    LLM_CHAT_STREAM_WITH_HISTORY = "llm_chat_stream_with_history"
    LLM_CHAT_STREAM_WITH_HISTORY_AND_CONTEXT = "llm_chat_stream_with_history_and_context"


# Example usage
class Model(BaseModel):
    model_name:str
    model_version:str
    model_provider:str
    model_type: ModelType

  
class Config(BaseModel):
    api_key: str
    model:Model
    system_prompt:str


import json
instance = Config(api_key="123", model=Model(model_name="test", model_version="1.0", model_provider="test", model_type=ModelType.LLM), system_prompt="test")
schema = instance.model_json_schema()
print(f"schema:\n\n{json.dumps(schema, indent=2)}")
DynamicModel = create_model_from_schema(schema, globals_dict=globals())
print(f"DynamicModel:\n\n{json.dumps(DynamicModel.model_json_schema(), indent=2)}")

# Force enums to their values (strings) when dumping for DynamicModel instantiation
dumped_json_str = instance.model_dump_json() # instance.model_dump(mode='json') returns a string
instance2 = DynamicModel(**json.loads(dumped_json_str))
print(instance2.model_dump())
# Verify equivalence
import json
assert DynamicModel.model_json_schema() == schema
# print(f"instance2:\n\n{json.dumps(instance2.model_dump_json(), indent=2)}\n\ninstance:\n\n{json.dumps(instance.model_dump_json(), indent=2)}")
