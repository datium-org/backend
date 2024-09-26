from enum import Enum
import urllib, urllib.request
from user_bridge_api.src.utils.types import DataType, DataTypeExtensions
from datetime import datetime
import pandas as pd

class Document:
  """
  Document Class:
    Handles document categorization/tags
  """
  def __init__(self, id: str, category, title, summary, date_added, file_url, doc_path="docs"):
    self.id = id
    self.category = category
    self.title = title
    self.summary = summary
    self.date_added = datetime.now()
    self.file_url = file_url
    self.doc_path = doc_path

  def download_file(self):
    file_Path = f'{self.doc_path}/{self.id}.pdf'
    urllib.request.urlretrieve(self.file_url, file_Path)

  def to_dict(self) -> dict:
    return {
      "chunk":(self.title + "\n" + self.summary),
      "metadata":{"title": self.title, "file_url": self.date_added, "date_added": self.date_added, "category": self.category},
      "id":str(self.id)
    }
  
  def __str__(self):
    return f"Category: {self.category}. Document Title: {self.title}. Published On: {self.date_added}. File URL: {self.file_url}"