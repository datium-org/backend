from concurrent import futures
import grpc
import logging
from dotenv import load_dotenv
import os
from fastapi import APIRouter, FastAPI, File, UploadFile

from typing import Annotated
import uvicorn
from pydantic import BaseModel
import yaml

from db.src.aws.postgres import Postgres
from db.src.manager import OrganizationManager, PublicManager
from db.src.table import TableManager, TDataHierarchyManager, TFileManagementManager, TOrganizationsManager
from db.src.schema import SchemaManager

import db.src.utils.types as types
import db.src.utils.paths as paths

router = APIRouter()

load_dotenv()

logging.basicConfig(level=logging.DEBUG, filename=os.path.join(paths.db_service_path, 'logs/std.log'), filemode='w', format='%(asctime)s: %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(name="server")

config_path = os.path.join(os.getcwd(), paths.db_config_path, "db.yaml")

with open(config_path) as stream:
  db_config = dict(yaml.safe_load(stream))

db = Postgres(**db_config)

db.connect()

psm = PublicManager(db)


@router.post("/org/create")
async def org_create(organization: types.Organization):
  psm.create_organization(organization)
  return {"response": "success"}

@router.post("/org/hierarchy/add")
async def org_hierarchy_add(organization: types.Organization):
  psm.create_organization(organization)
  return {"response": "success"}


@router.post("/org/file/add")
async def org_add_file(organization: types.Organization):
  psm.get_organization(**organization.model_dump())
  return {"response": "success"}

@router.post("/org/file/remove")
async def org_remove_file(organization: types.Organization):
  psm.create_organization(**organization.model_dump())
  return {"response": "success"}


@router.get("/")
async def root():
  return {"response": "db service"}