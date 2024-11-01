from abc import ABC, abstractmethod
from file import File, DataSource
from pydrive.drive import GoogleDrive



class SourceLoader(ABC):
  def __init__(self, source):
    self._source = source

  @abstractmethod
  def load_file(file: File):
    pass

  @classmethod
  def get_loader(cls, data_source: DataSource, *args, **kwargs):
    if data_source == DataSource.DRIVE:
      return DriveLoader(*args, **kwargs)
    

class DriveLoader(SourceLoader):
  def __init__(self, source: GoogleDrive):
    super().__init__(source)
    
  def load_file(self, file: File):
    g_file = file.to_gdrive_file(self._source)
    g_file.GetContentFile(file.title) # save file