from concurrent import futures
import logging
from dotenv import load_dotenv
import os
from fastapi import APIRouter, FastAPI, File, UploadFile
from typing import Annotated
import uvicorn

from intelligence.src.llm import LLM
from intelligence.src.embeddings import Embedding

import intelligence.src.utils.paths as paths
import intelligence.src.utils.types as types

router = APIRouter()

load_dotenv()

logging.basicConfig(level=logging.DEBUG, filename=os.path.join(paths.int_service_path, 'logs/std.log'), filemode='w', format='%(asctime)s: %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(name="server")

# ========================
# LLM Servicer
# ========================

@router.post("/llm/query")
async def llm_query(request: types.QueryRequest):
  logging.info(f"User: {request.user_id}")

  llm_client = LLM(request.llm_config)

  response = llm_client.query(request.query, request.system_message)
  return {"response": response}



# ========================
# Embedding Servicer
# ========================

@router.post("/embedding/embed")
async def embedding_embed(request: types.EmbedRequest):
  logging.info(f"User: {request.user_id}")


  embedding_client = Embedding(request.embedding_config)


  embeddings = embedding_client.embed_texts(request.texts)

  return {"response": embeddings}


@router.get("/")
async def root():
  return {"response": "intelligence service"}

