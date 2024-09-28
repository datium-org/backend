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


    self.columns = self.load_table_columns()

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

  def load_table_columns(self) -> List[str]:
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