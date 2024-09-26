import psycopg2
from psycopg2 import sql
from typing import Optional, Tuple, List, Any
import yaml
import os
import abc
from datetime import datetime
import json
import uuid

from db.src.aws.postgres import Postgres




class TableManager:
  def __init__(self, table_name: str, schema_name: str, db: Postgres) -> None:
    self.table_name = table_name
    self.schema_name = schema_name
    self.db = db

  def add_row(self, columns: List[str], values: List[Any]) -> None:
    """Insert a new row into a table in the user's schema."""
    query = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
      sql.Identifier(self.schema_name),
      sql.Identifier(self.table_name),
      sql.SQL(', ').join(map(sql.Identifier, columns)),
      sql.SQL(', ').join(sql.Placeholder() * len(values))
    )
    self.db.execute_query(query.as_string(self.db.connection), tuple(values))

  def update_row(self, set_column: str, set_value: Any, condition_column: str, condition_value: Any) -> None:
    """Update a row in a table in the user's schema based on a condition."""
    query = sql.SQL("UPDATE {}.{} SET {} = %s WHERE {} = %s").format(
      sql.Identifier(self.schema_name),
      sql.Identifier(self.table_name),
      sql.Identifier(set_column),
      sql.Identifier(condition_column)
    )
    self.db.execute_query(query.as_string(self.db.connection), (set_value, condition_value))

  def get_row(self, condition_column: str, condition_value: Any) -> Optional[Tuple[Any, ...]]:
    """Retrieve a single row from the user's table based on a condition."""
    query = sql.SQL("SELECT * FROM {}.{} WHERE {} = %s LIMIT 1").format(
      sql.Identifier(self.schema_name),
      sql.Identifier(self.table_name),
      sql.Identifier(condition_column)
    )
    return self.db.fetch_one(query.as_string(self.db.connection), (condition_value,))

  def delete_row(self, condition_column: str, condition_value: Any) -> None:
    """Delete a row from a table in the user's schema based on a condition."""
    query = sql.SQL("DELETE FROM {}.{} WHERE {} = %s").format(
      sql.Identifier(self.schema_name),
      sql.Identifier(self.table_name),
      sql.Identifier(condition_column)
    )
    self.db.execute_query(query.as_string(self.db.connection), (condition_value,))

  def get_table_columns(self) -> List[str]:
    """Helper function to get the column names of a given table in the user's schema."""
    query = sql.SQL("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = %s AND table_schema = %s
    """)
    columns = self.db.fetch_all(query, (self.table_name, self.schema_name))
    return [column[0] for column in columns]
  
  @classmethod
  def is_table_exists(cls, table_name: str, schema_name: str, db: Postgres) -> bool:
    query = sql.SQL("""
    SELECT EXISTS (
      SELECT 1
      FROM information_schema.tables
      WHERE table_schema = %s
      AND table_name = %s
    )""")
    
    params = (schema_name, table_name)

    exists = db.fetch_one(query.as_string(db.connection), params)[0]

    return exists

  @classmethod
  def get_table_manager(cls, table_name, schema_name, db):
    if table_name == TOrganizationsManager.table_name:
      return TOrganizationsManager(schema_name, db)
    elif table_name == TDataHierarchyManager.table_name:
      if TableManager.is_table_exists(table_name, schema_name, db):
        return TDataHierarchyManager(schema_name, db)
    elif table_name == TFileManagementManager.table_name:
      if TableManager.is_table_exists(table_name, schema_name, db):
        return TFileManagementManager(schema_name, db)
    raise NotADirectoryError(f"Table does not exist: {schema_name}.{table_name}")
  



class TOrganizationsManager(TableManager):
  """'public.organizations' table manager"""

  table_name = "organizations"

  def __init__(self, schema_name: str, db: Postgres):
    super().__init__(TDataHierarchyManager.table_name, schema_name, db)

  def is_organization_exists(self, organization_email: str):
    row = self.get_row("email", organization_email)
    print(row)




class TDataHierarchyManager(TableManager):
  """'{organization}.datahierarchy' table manager"""

  table_name = "datahierarchy"

  def __init__(self, schema_name: str, db: Postgres):
    super().__init__(TDataHierarchyManager.table_name, schema_name, db)

  def add_node(self, parent_id: Optional[int], name: str) -> int:
    query = sql.SQL("""
      INSERT INTO {}.{} (parent_id, name)
      VALUES (%s, %s)
      RETURNING id""").format(
        sql.Identifier(self.schema_name),
        sql.Identifier(self.table_name),
      )
    params = (parent_id, name)

    node_id = self.db.fetch_one(query.as_string(self.db.connection), params)[0]

    return node_id

  def remove_node(self, node_id: int) -> None:
    query = sql.SQL("""DELETE FROM {}.{} WHERE id = %s""").format(
      sql.Identifier(self.schema_name),
      sql.Identifier(self.table_name),
    )
    params = (node_id,)

    self.db.execute_query(query.as_string(self.db.connection), params)
    

  def get_descendants(self, node_id: int) -> List[Tuple[int, int, str]]:
    query = sql.SQL("""
      WITH RECURSIVE descendants AS (
        SELECT id, parent_id, name
        FROM {}.{}
        WHERE id = %s
        UNION ALL
        SELECT n.id, n.parent_id, n.name
        FROM {}.{} n
        INNER JOIN descendants d ON n.parent_id = d.id
      )
      SELECT * FROM descendants""").format(
        sql.Identifier(self.schema_name),
        sql.Identifier(self.table_name),
        sql.Identifier(self.schema_name),
        sql.Identifier(self.table_name),
      )
    params = (node_id,)
  
    rows = self.db.fetch_all(query, params)
    
    return rows
  
  def get_ancestors(self, node_id: int) -> List[Tuple[int, int, str]]:
    query = sql.SQL("""
      WITH RECURSIVE ancestors AS (
        SELECT id, parent_id, name
        FROM {}.{}
        WHERE id = %s
        UNION ALL
        SELECT n.id, n.parent_id, n.name
        FROM {}.{} n
        INNER JOIN ancestors a ON n.id = a.parent_id
      )
      SELECT * FROM ancestors""").format(
        sql.Identifier(self.schema_name),
        sql.Identifier(self.table_name),
        sql.Identifier(self.schema_name),
        sql.Identifier(self.table_name),
      )
    
    params = (node_id,)
    
    rows = self.db.fetch_all(query, params)
    
    return rows

  def get_full_tree(self) -> List[Tuple[int, int, str]]:
    query = sql.SQL("""
      WITH RECURSIVE tree AS (
        SELECT id, parent_id, name
        FROM {}.{}
        WHERE parent_id IS NULL
        UNION ALL
        SELECT n.id, n.parent_id, n.name
        FROM {}.{} n
        INNER JOIN tree t ON n.parent_id = t.id
      )
      SELECT * FROM tree""").format(
        sql.Identifier(self.schema_name),
        sql.Identifier(self.table_name),
        sql.Identifier(self.schema_name),
        sql.Identifier(self.table_name),
      )
    
    rows = self.db.fetch_all(query, ())
    
    return rows
  




class TFileManagementManager(TableManager):
  """'{organization}.filemanagement' table manager"""

  table_name = "filemanagement"

  def __init__(self, schema_name: str, db: Postgres):
    super().__init__(TFileManagementManager.table_name, schema_name, db)
