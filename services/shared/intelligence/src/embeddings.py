import os
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import argparse
import dotenv
import langchain
import logging
from transformers import AutoModel
from typing import Tuple

# For Testing Purposes...
langchain.debug = True
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(name="embeddings")


class Embedding():
  """
  A class that integrates with the Cohere API for conversational AI purposes.

  Attributes:
    __conversation_id (str): Unique ID for tracking the conversation.
    __embedding Union(IndexEmbedding, ChromaEmbedding): an embedding system for the RAG to use
    __max_tokens int: max number of tokns a response to a query can be
  """

  def __init__(self, embedding_model: Tuple[str, str] = ("openai", "text-embedding-3-small"), *args, **kwargs):
    """
    Initializes the Chat class, setting up the embedding model used for queries.

    Args:
      num_matches (int): Number of matching documents to return upon a query.
    """
    dotenv.load_dotenv()
    self.__openai_key = os.getenv(f'OPENAI_API_KEY')
    self.__openai_org = os.getenv(f'OPENAI_ORG')

    if embedding_model[0].lower() == "openai":
      self.__client = OpenAIEmbeddings(
          api_key=self.__openai_key,
          model=embedding_model[1],
          organization=self.__openai_org),
      
    elif (embedding_model[0].lower() == "hf") or (embedding_model[0].lower() == "huggingface"):
      self.__client = HuggingFaceEmbeddings(
        model_name=embedding_model[1],
        model_kwargs={"trust_remote_code":True})
      

  def embed_texts(self, texts: list[str]) -> list[list[float]]:
    """
    Embed a list of documents.

    Args:
      query (str): The query string.

    Returns:
      str: The response from the language model.
    """


    embeddings = self.__client.embed_documents(texts)
    logging.info(f"Embeddings Result: {len(embeddings), len(embeddings[0])}")

    return embeddings
    
  
  def embed_query(self, query: str) -> list[float]:
    """
    Embed a list of documents.

    Args:
      query (str): The query string.

    Returns:
      str: The response from the language model.
    """

    embeddings = self.__client.embed_query(query)
    logging.info(f"Embeddings Result: {len(embeddings)}")

    return embeddings





if __name__ == "__main__":
  embedding = Embedding(embedding_provider="hf", )
  
  print(embedding.embed_texts(["hello"]))
