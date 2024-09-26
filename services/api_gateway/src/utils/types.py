from enum import Enum
import urllib, urllib.request

class DataType(Enum):
  TABULAR="Tabular"
  NL="Natural Language"
  SV="Semi-Visual"
  AV="Audio-Visual"

class DataTypeExtensions(Enum):
  TABULAR=[".csv", ".xlsx", ".xls"]
  NL=[".pdf", ".doc", ".docx", ".txt", ".html", ".json"]
  SV=[".pptx", ".ppt", ".pdf"]
  AV=[".mp3", ".mp4", ".wav", ".mov"]


