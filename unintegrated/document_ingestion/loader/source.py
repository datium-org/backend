from abc import ABC, abstractmethod
from file.file import File, DataSource

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile


class SourceLoader(ABC):
  def __init__(self, *args, **kwargs):
    self._source = self._create_source(*args, **kwargs)

  @abstractmethod
  def _create_source(self):
    pass

  @abstractmethod
  def load_file(file: File):
    pass

  @abstractmethod
  def get_file(file_id: str = None, file_name: str = None) -> File:
    pass

  @classmethod
  def get_loader(cls, data_source: DataSource, *args, **kwargs):
    if data_source == DataSource.DRIVE:
      return DriveLoader(*args, **kwargs)
    

class DriveLoader(SourceLoader):
  def __init__(self, host_name: str = "localhost", port_numbers: list[int] = [8080], *args, **kwargs):
    super().__init__(host_name, port_numbers, *args, **kwargs)

  def _create_source(self, host_name: str = "localhost", port_numbers: list[int] = [8080]):
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth(host_name=host_name, port_numbers=port_numbers)
    drive = GoogleDrive(gauth)
    return drive
    
  def load_file(self, file: File):
    g_file = file.to_gdrive_file(self._source)
    g_file.GetContentFile(file.title) # save file

  def get_file(self, file_id: str = None, file_name: str = None) -> File:
    if file_id:
      g_file = self._source.CreateFile({'id': file_id})
    elif file_name:
      g_file = self._source.CreateFile({'title': file_name})
    else:
      raise ValueError("Either file_id or file_name must be provided")
    
    return File.from_gdrive_file(g_file)
    
  def iterate_files(self, pagination: int = 10):
    # Paginate file lists by specifying number of max results
    for file_list in self._source.ListFile({'maxResults': pagination}):
      print (f'Received {len(file_list)} files from Files.list()')
      file_list = [File.from_gdrive_file(file) for file in file_list]
      yield file_list