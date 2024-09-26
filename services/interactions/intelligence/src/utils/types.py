from pydantic import BaseModel
from datetime import datetime
import json
from typing import Tuple

class QueryRequest(BaseModel):
  query: str
  system_message: str
  llm_config: Tuple[str, str]
  user_id: str

class EmbedRequest(BaseModel):
  texts: list[str]
  embedding_config: Tuple[str, str]
  user_id: str