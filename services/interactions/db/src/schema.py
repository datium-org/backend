from psycopg2 import sql
from typing import Optional, Tuple, List, Any
import abc
import yaml

from db.src.aws.postgres import Postgres

class SchemaManager(abc.ABC):
  def __init__(self, schema_name: str, db: Postgres) -> None:
    self.schema_name = schema_name
    self.db = db

  def create_table_from_yaml(self, yaml_file_path: str) -> None:
    # Load the YAML file
    with open(yaml_file_path, 'r') as file:
      yaml_data: list[dict] = yaml.safe_load(file)

    # Extract table information
    for i in range(0, len(yaml_data)):
      table_name = yaml_data[i]['table_name']
      columns = yaml_data[i]['columns']

      # Construct the CREATE TABLE query
      column_definitions = []

      for column in columns:
        if 'KEY' in column['name']:
          # Handle foreign key constraint
          column_definitions.append(sql.SQL(f"{column['name']} {column['type']}").as_string(self.db.connection))
        else:
          # Regular column definition
          column_definitions.append(sql.SQL("{} {}").format(
            sql.Identifier(column['name']),
            sql.SQL(column['type'])
          ).as_string(self.db.connection))
      
      print(table_name)
      print(column_definitions)

      if yaml_data[i].get("partition"):
        print(yaml_data[i]["partition"])
        by = yaml_data[i]["partition"]["by"]
        partitions: list = yaml_data[i]["partition"]["partitions"]

        self.create_table(table_name, column_definitions, partition_by=by)

        for partition in partitions:
          partition_name = partition["name"]
          partition_for_with = partition["for_with"]
          self.create_partition(partition_name, table_name, partition_for_with)

      else:
        self.create_table(table_name, column_definitions)

  def create_partition(self, partition_name: str, table_name: str, for_with: str):
    """Create a new partitioned table within the user's schema."""

    query = sql.SQL("CREATE TABLE {}.{} PARTITION OF {}.{} FOR {}").format(
      sql.Identifier(self.schema_name),
      sql.Identifier(partition_name),
      sql.Identifier(self.schema_name), 
      sql.SQL(table_name),
      sql.SQL(for_with)
    )

    query_str = query.as_string(self.db.connection)

    print(query_str)

    self.db.execute_query(query_str)

  def create_table(self, table_name: str, columns: List[str], partition_by: str = None) -> None:
    """Create a new table within the user's schema."""
    column_definitions = ", ".join(columns)
    
    query = sql.SQL("CREATE TABLE IF NOT EXISTS {}.{} ({})").format(
      sql.Identifier(self.schema_name),
      sql.Identifier(table_name),
      sql.SQL(column_definitions)
    )

  
    query_str = query.as_string(self.db.connection)

    if partition_by:
      query_str += f" PARTITION BY {partition_by}"

    print(query_str)
    
    self.db.execute_query(query_str)
  
  def print_table(self, table_name: str) -> None:
    """Fetch and print all rows from the specified table in the user's schema with aligned columns."""
    # Fetch the column names
    columns_query = sql.SQL("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = %s AND table_schema = %s
    """)
    columns = self.db.fetch_all(columns_query, (table_name, self.schema_name))
    column_names = [column[0] for column in columns]

    # Fetch all rows from the table
    table_query = sql.SQL("SELECT * FROM {}.{}").format(
      sql.Identifier(self.schema_name),
      sql.Identifier(table_name)
    )
    rows = self.db.fetch_all(table_query)

    # Determine the maximum width for each column
    column_widths = [len(column) for column in column_names]
    for row in rows:
      for i, value in enumerate(row):
        column_widths[i] = max(column_widths[i], len(str(value)))

    # Create a format string for rows and headers
    row_format = " | ".join(["{:<" + str(width) + "}" for width in column_widths])

    # Print the header row
    print(row_format.format(*column_names))
    print("-" * (sum(column_widths) + 3 * (len(column_widths) - 1)))

    # Print each data row
    for row in rows:
      print(row_format.format(*map(str, row)))

    print()  # Add a newline for separation
