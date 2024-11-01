from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import json

from db import Postgres, SchemaManager

class FileSystemManager:
  def __init__(self, schema_name: str, db: Postgres):
    self.schema_name = schema_name
    self.db = db
    self.setup_tables()

  def setup_tables(self) -> None:
    """Initialize the database tables using the schema manager."""
    # First enable UUID extension
    enable_uuid_query = "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
    self.db.execute_query(enable_uuid_query)
    
    schema_manager = SchemaManager(self.schema_name, self.db)
    schema_manager.create_table_from_yaml('file_system_schema.yaml')  # Your schema file path

  def create_folder(self, name: str, parent_id: Optional[uuid.UUID] = None) -> uuid.UUID:
    """Create a new folder and set up its hierarchical relationships."""
    # Create the folder
    folder_id = uuid.uuid4()
    query = f"""
    INSERT INTO {self.schema_name}.folders (folder_id, name) 
    VALUES (%s, %s) 
    RETURNING folder_id
    """
    self.db.execute_query(query, (folder_id, name))

    # Insert closure table entries
    if parent_id:
      # Copy existing paths from parent
      query = f"""
      INSERT INTO {self.schema_name}.folder_closure (ancestor_id, descendant_id, depth)
      SELECT ancestor_id, %s, depth + 1
      FROM {self.schema_name}.folder_closure
      WHERE descendant_id = %s
      """
      self.db.execute_query(query, (folder_id, parent_id))

    # Insert self-reference path
    query = f"""
    INSERT INTO {self.schema_name}.folder_closure (ancestor_id, descendant_id, depth)
    VALUES (%s, %s, 0)
    """
    self.db.execute_query(query, (folder_id, folder_id))

    return folder_id

  def add_file(self, folder_id: uuid.UUID, name: str, file_type: str, 
               size_bytes: int, metadata: Dict[str, Any]) -> uuid.UUID:
    """Add a new file to a folder."""
    file_id = uuid.uuid4()
    query = """
    INSERT INTO {}.files 
    (file_id, folder_id, name, file_type, size_bytes, metadata)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING file_id
    """.format(self.schema_name)
    
    self.db.execute_query(
      query, 
      (file_id, folder_id, name, file_type, size_bytes, json.dumps(metadata))
    )
    return file_id

  def get_folder_contents(self, folder_id: uuid.UUID) -> Dict[str, List]:
    """Get all files and subfolders in a folder."""
    # Get subfolders
    folder_query = """
    SELECT f.folder_id, f.name
    FROM {}.folder_closure fc
    JOIN {}.folders f ON f.folder_id = fc.descendant_id
    WHERE fc.ancestor_id = %s AND fc.depth = 1
    """.format(self.schema_name, self.schema_name)
    
    folders = self.db.fetch_all(folder_query, (folder_id,))

    # Get files
    file_query = """
    SELECT file_id, name, file_type, size_bytes, metadata
    FROM {}.files
    WHERE folder_id = %s
    """.format(self.schema_name)
    
    files = self.db.fetch_all(file_query, (folder_id,))

    return {
      'folders': [{'id': str(f[0]), 'name': f[1]} for f in folders],
      'files': [
        {
          'id': str(f[0]),
          'name': f[1],
          'type': f[2],
          'size': f[3],
          'metadata': f[4]
        } for f in files
      ]
    }

  def move_folder(self, folder_id: uuid.UUID, new_parent_id: uuid.UUID) -> None:
    """Move a folder to a new parent folder."""
    # First, remove old closure entries
    delete_query = """
    DELETE FROM {}.folder_closure 
    WHERE descendant_id IN (
      SELECT descendant_id 
      FROM {}.folder_closure 
      WHERE ancestor_id = %s
    )
    AND ancestor_id IN (
      SELECT ancestor_id 
      FROM {}.folder_closure 
      WHERE descendant_id = %s
      AND ancestor_id != descendant_id
    )
    """.format(self.schema_name, self.schema_name, self.schema_name)
    
    self.db.execute_query(delete_query, (folder_id, folder_id))

    # Then insert new closure entries
    insert_query = """
    INSERT INTO {}.folder_closure (ancestor_id, descendant_id, depth)
    SELECT a.ancestor_id, d.descendant_id, a.depth + d.depth + 1
    FROM {}.folder_closure a
    CROSS JOIN {}.folder_closure d
    WHERE a.descendant_id = %s
    AND d.ancestor_id = %s
    """.format(self.schema_name, self.schema_name, self.schema_name)
    
    self.db.execute_query(insert_query, (new_parent_id, folder_id))

  def delete_folder(self, folder_id: uuid.UUID) -> None:
    """Delete a folder and all its contents."""
    # First delete all files in the folder and its subfolders
    files_delete_query = """
    DELETE FROM {}.files
    WHERE folder_id IN (
      SELECT descendant_id
      FROM {}.folder_closure
      WHERE ancestor_id = %s
    )
    """.format(self.schema_name, self.schema_name)
    
    self.db.execute_query(files_delete_query, (folder_id,))

    # Then delete the folder closure relationships
    closure_delete_query = """
    DELETE FROM {}.folder_closure
    WHERE descendant_id IN (
      SELECT descendant_id
      FROM {}.folder_closure
      WHERE ancestor_id = %s
    )
    """.format(self.schema_name, self.schema_name)
    
    self.db.execute_query(closure_delete_query, (folder_id,))

    # Finally delete the folder itself
    folder_delete_query = """
    DELETE FROM {}.folders
    WHERE folder_id = %s
    """.format(self.schema_name)
    
    self.db.execute_query(folder_delete_query, (folder_id,))

  def print_tree(self, root_id: Optional[uuid.UUID] = None, level: int = 0) -> None:
    """
    Print the entire file system tree starting from the given root.
    If no root_id is provided, prints all root-level folders.
    
    Args:
        root_id: UUID of the starting folder (optional)
        level: Current indentation level (used recursively)
    """
    # Get root folders if no root_id provided
    if root_id is None:
      query = f"""
      SELECT folder_id, name
      FROM {self.schema_name}.folders
      WHERE folder_id NOT IN (
        SELECT DISTINCT descendant_id
        FROM {self.schema_name}.folder_closure
        WHERE ancestor_id != descendant_id
      )
      ORDER BY name
      """
      root_folders = self.db.fetch_all(query)
      
      print("\n📁 File System Tree:")
      for folder in root_folders:
        self._print_folder_contents(folder[0], folder[1], 0)
      print()
      return

    # If root_id provided, print that subtree
    query = f"""
    SELECT name 
    FROM {self.schema_name}.folders 
    WHERE folder_id = %s
    """
    folder_name = self.db.fetch_one(query, (root_id,))[0]
    self._print_folder_contents(root_id, folder_name, level)

  def _print_folder_contents(self, folder_id: uuid.UUID, folder_name: str, level: int) -> None:
    """
    Recursively print folder contents with proper indentation.
    
    Args:
      folder_id: UUID of the current folder
      folder_name: Name of the current folder
      level: Current indentation level
    """
    indent = "    " * level
    
    # Print current folder
    print(f"{indent}📁 {folder_name}/")

    # Get and print files in current folder
    files_query = f"""
    SELECT name, file_type, size_bytes
    FROM {self.schema_name}.files
    WHERE folder_id = %s
    ORDER BY name
    """
    files = self.db.fetch_all(files_query, (folder_id,))
    
    for file in files:
      name, file_type, size = file
      size_str = self._format_size(size)
      print(f"{indent}    📄 {name} ({file_type}, {size_str})")

    # Get and recursively print subfolders
    subfolders_query = f"""
    SELECT f.folder_id, f.name
    FROM {self.schema_name}.folder_closure fc
    JOIN {self.schema_name}.folders f ON f.folder_id = fc.descendant_id
    WHERE fc.ancestor_id = %s
    AND fc.depth = 1
    ORDER BY f.name
    """
    subfolders = self.db.fetch_all(subfolders_query, (folder_id,))
    
    for subfolder in subfolders:
      self._print_folder_contents(subfolder[0], subfolder[1], level + 1)

  def _format_size(self, size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
      if size_bytes < 1024:
        return f"{size_bytes:.1f}{unit}"
      size_bytes /= 1024
    return f"{size_bytes:.1f}PB"