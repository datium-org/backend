from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import datetime
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile

class DataSource(Enum):
  DRIVE="GoogleDrive"
  ONEDRIVE="OneDrive"
  GMAIL="Gmail"
  MANUAL="Manual"


# Read-only File
class File(BaseModel):
  title: str = Field(..., description="File name")
  source: DataSource = Field(..., description="File source")
  source_id: str = Field(..., description="Id of the file in the source")
  extension: str = Field(..., description="File extension")
  size: int = Field(..., description="Size in bytes")
  created_date: datetime = Field(..., description="Created date")
  modified_date: datetime = Field(..., description="Modified date")
  last_viewed_by_me: datetime = Field(..., description="Last viewed by me date")
  content: Optional[str] = None  # Content can be loaded lazily

  def to_gdrive_file(self, drive: GoogleDrive) -> GoogleDriveFile:
    """Turn the file into a Google Drive File."""
    # Download the file from the corresponding source
    file = drive.CreateFile({"title": self.title})
    return file
  
  @classmethod
  def from_gdrive_file(self, file: GoogleDriveFile):
    title = file["title"]
    source_id = file["id"]
    extension = file["fileExtension"]
    size = file["fileSize"]
    created_date = file["createdDate"]
    modified_date = file["modifiedDate"]
    last_viewed_by_me = file["lastViewedByMeDate"]

    return File(title, DataSource.DRIVE, source_id, extension, size, created_date, modified_date, last_viewed_by_me)
  



