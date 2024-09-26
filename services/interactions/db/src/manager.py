from psycopg2 import sql
from typing import Optional, Tuple, List, Any
import yaml
import os

from db.src.table import TableManager
from db.src.schema import SchemaManager
from db.src.aws.postgres import Postgres

import db.src.utils.security as security
import db.src.utils.types as types
import db.src.utils.paths as paths


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