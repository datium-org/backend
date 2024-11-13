from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from enum import Enum
import datetime
import json
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile

class DataSource(Enum):
  DRIVE="GoogleDrive"
  ONEDRIVE="OneDrive"
  GMAIL="Gmail"
  MANUAL="Manual"

class FileExtensions(Enum):
  PDF = "pdf"
  DOCX = "docx"
  DOC = "doc"
  TXT = "txt"
  CSV = "csv"
  XLSX = "xlsx"
  XLS = "xls"
  JPG = "jpg"
  PNG = "png"
  SVG = "svg"
  HTML = "html"
  XML = "xml"
  JSON = "json"

class FileObject:
  def __init__(self) -> None:
    self.text_sections = []
    self.tables = []
    self.images = []

  def __str__(self) -> str:
    return f"Text sections: {self.text_sections}, Tables: {self.tables}, Images: {self.images}"
  
  def tables_to_json(self) -> json:
    return self.tables
  

# Read-only File
class File(BaseModel):
  title: str = Field(..., description="File name")
  source: DataSource = Field(..., description="File source")
  source_id: str = Field(..., description="Id of the file in the source")
  mime_type: str = Field(..., description="MIME type")
  size: int = Field(..., description="Size in bytes")
  created_date: datetime = Field(..., description="Created date")
  modified_date: datetime = Field(..., description="Modified date")
  last_viewed_by_me: datetime = Field(..., description="Last viewed by me date")
  summary: Optional[str] = None
  content: Optional[FileObject] = None  # Content can be loaded lazily

  model_config = ConfigDict(arbitrary_types_allowed=True)

  def to_gdrive_file(self, drive: GoogleDrive) -> GoogleDriveFile:
    """Turn the file into a Google Drive File."""
    # Download the file from the corresponding source
    file = drive.CreateFile({"title": self.title})
    return file
  
  @classmethod
  def from_gdrive_file(cls, file: GoogleDriveFile):
    title = file.get("title", "")
    source_id = file.get("id", "")
    mime_type = file.get("mimeType", "")
    size = file.get("fileSize", 0)
    created_date = file.get("createdDate", None)
    modified_date = file.get("modifiedDate", None)
    last_viewed_by_me = file.get("lastViewedByMeDate", None)

    return File(
      title=title, 
      source=DataSource.DRIVE, 
      source_id=source_id, 
      mime_type=mime_type, 
      size=size, 
      created_date=created_date, 
      modified_date=modified_date, 
      last_viewed_by_me=last_viewed_by_me
    )



