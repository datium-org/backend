import psycopg2
from psycopg2 import sql
from typing import Optional, Tuple, List, Any
import yaml
import os
import abc
from datetime import datetime
import json
import uuid


class Postgres:
  def __init__(self, dbname: str, user: str, password: str, host: str, port: str = '5432') -> None:
    """Initialize connection parameters."""
    self.dbname = dbname
    self.user = user
    self.password = password
    self.host = host
    self.port = port
    self.connection: Optional[psycopg2.extensions.connection] = None

  def connect(self) -> None:
    """Establish database connection."""
    self.connection = psycopg2.connect(
      dbname=self.dbname,
      user=self.user,
      password=self.password,
      host=self.host,
      port=self.port
    )
    self.connection.autocommit = True  # Automatically commit changes

  def close(self) -> None:
    """Close database connection."""
    if self.connection:
      self.connection.close()

  def execute_query(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> None:
    """Execute a given query with optional parameters."""
    with self.connection.cursor() as cursor:
      cursor.execute(query, params)

  def fetch_all(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> List[Tuple[Any, ...]]:
    """Fetch all results from the executed query."""
    with self.connection.cursor() as cursor:
      cursor.execute(query, params)
      return cursor.fetchall()

  def fetch_one(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Tuple[Any, ...]]:
    """Fetch a single result from the executed query."""
    with self.connection.cursor() as cursor:
      cursor.execute(query, params)
      return cursor.fetchone()

  def view_public_tables(self) -> List[Tuple[str]]:
    """Return a list of all tables in the database."""
    query = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    """
    return self.fetch_all(query)




