from concurrent import futures
import grpc
import logging
from dotenv import load_dotenv
import os
from fastapi import FastAPI, File, UploadFile, APIRouter
from typing import Annotated
import uvicorn

router = APIRouter()

load_dotenv()


logging.basicConfig(level=logging.DEBUG, filename='logs/std.log', filemode='w', format='%(asctime)s: %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(name="server")

@router.get("/")
async def root():
  return {"message": "Hello World"}
