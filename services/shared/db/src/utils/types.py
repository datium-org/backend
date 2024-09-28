from pydantic import BaseModel
from datetime import datetime
import json

# =================================
# Request Pydantic Models
# =================================

class Organization(BaseModel):
  name: str
  email: str
  password: str
  business_type: str
  date_created: datetime
  metadata: dict

  def to_list(cls) -> list[str]:
    return [cls.name, cls.email, cls.password, cls.business_type, cls.date_created, json.dumps(cls.metadata)]


class ChunkType(BaseModel):
  chunk: str
  id: str
  metadata: dict
  embedding: list[float]
