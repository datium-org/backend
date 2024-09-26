from psycopg2 import sql
from typing import Optional, Tuple, List, Any
import yaml
import os

from db_service.src.table import TableManager
from db_service.src.schema import SchemaManager
from db_service.src.aws.postgres import Postgres

import db_service.src.utils.security as security
import db_service.src.utils.types as types
import db_service.src.utils.paths as paths


class OrganizationsManager(SchemaManager):
  tables_path = os.path.join(os.getcwd(), paths.db_config_path, "organizations_tables.yaml")
  with open(tables_path) as stream:
    tables = list(yaml.safe_load(stream))

  schema_name = "organizations"

  def __init__(self, db: Postgres):
    super().__init__(f"organizations", db)
    self.organizations_tm = TableManager("organizations", OrganizationsManager.schema_name, db)
    self.file_management_tm = TableManager("file_management", OrganizationsManager.schema_name, db)

  def initialize_org(self, organization: types.Organization):
    pass

  def add_node(self, organization_id: int, parent: str, new_node: str, is_left=True):
    """ Adds a new node as the left or right child of the specified parent node."""
    tree: str = self.organizations_tm.get_row("organization_id", organization_id).get("data_hierarchy")

    def insert_at_position(position, insertion):
      return tree[:position] + insertion + tree[position:]

    position = tree.find(parent)
    if position == -1:
      raise ValueError(f"Parent node {parent} not found.")

    # Find the position to insert the new node
    insert_pos = tree.find('[', position) + 1
    if is_left:
      insert_pos += 0  # Insert as left child
    else:
      right_pos = tree.find(']', insert_pos)
      insert_pos = right_pos if right_pos > insert_pos else insert_pos

    insertion = f'{new_node}[]'
    if tree[insert_pos] != ']':
      insertion += ','

    self.organizations_tm.update_row(
       "data_hierarchy",
       insert_at_position(insert_pos, insertion),
       "organization_id",
       organization_id)  
  

  def remove_node(self, organization_id: int, node: str):
    """ Removes a node and its subtree from the tree string."""
    tree: str = self.organizations_tm.get_row("organization_id", organization_id).get("data_hierarchy")

    start_pos = tree.find(node)
    if start_pos == -1:
      raise ValueError(f"Node {node} not found.")

    # Find the opening bracket '['
    open_bracket = tree.find('[', start_pos)
    
    # Find the closing bracket for the current node's subtree
    balance = 1
    end_pos = open_bracket + 1
    while balance > 0:
      if tree[end_pos] == '[':
        balance += 1
      elif tree[end_pos] == ']':
        balance -= 1
      end_pos += 1

    # Remove the node and its subtree

    self.organizations_tm.update_row(
       "data_hierarchy",
       tree[:start_pos] + tree[end_pos:],
       "organization_id",
       organization_id)  

  def parse_tree(self, organization_id: int):
    """ Parses a tree in bracket notation into a nested dictionary structure."""
    def parse_subtree(subtree):
      node = ''
      children = []
      i = 0
      while i < len(subtree):
        if subtree[i] == '[':
          start_pos = i
          balance = 1
          while balance > 0:
            i += 1
            if subtree[i] == '[':
              balance += 1
            elif subtree[i] == ']':
              balance -= 1
          children.append(parse_subtree(subtree[start_pos+1:i]))
        else:
          node += subtree[i]
        i += 1
      return {node: children}
    
    tree: str = self.organizations_tm.get_row("organization_id", organization_id).get("data_hierarchy")
    return parse_subtree(tree)

class PublicManager(SchemaManager):
  tables_path = os.path.join(os.getcwd(), paths.db_config_path, "public_tables.yaml")
  with open(tables_path) as stream:
    tables = list(yaml.safe_load(stream))

  schema_name = "public"

  def __init__(self, db: Postgres):
    super().__init__(PublicManager.schema_name, db)
    self.organizations_tm = TableManager("organizations", PublicManager.schema_name, db)

  # not defined
  def create_schema(self) -> None:
    pass

  # not defined
  def drop_schema(self) -> None:
    pass

  def create_organization(self, organization: types.Organization):
    # add new user to user info table
    om = OrganizationsManager(db)

    # add row if doesnt exist already
    # if self.organizations_tm.
    self.organizations_tm.add_row(columns=self.organizations_tm.columns[1:], values=organization.to_list())

    print(self.organizations_tm.get_row())

    # om.organizations_tm.add_row(columns=om.organizations_tm.columns, values=[])


# Example Usage
if __name__ == "__main__":

  with open(os.path.join(os.getcwd(), paths.db_config_path, "db.yaml")) as stream:
    db_config = dict(yaml.safe_load(stream))

  db = Postgres(**db_config)
  db.connect()
  
  org = OrganizationsManager(db)

  org.create_table_from_yaml(os.path.join(os.getcwd(), paths.db_config_path, "organizations_tables.yaml"))

  db.close()