from concurrent import futures
import grpc
import logging
from dotenv import load_dotenv
import os
from fastapi import FastAPI, File, UploadFile
from typing import Annotated
import uvicorn

app = FastAPI()


load_dotenv()


logging.basicConfig(level=logging.DEBUG, filename='logs/std.log', filemode='w', format='%(asctime)s: %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(name="server")

@app.get("/")
async def root():
  return {"message": "Hello World"}

if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=8000)