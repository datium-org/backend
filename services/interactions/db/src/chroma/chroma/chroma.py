import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import numpy as np
from db_api.utils.types import ChunkType
import os

class ChromaEmbeddingFunction(EmbeddingFunction):
  def __call__(self, input: Documents) -> Embeddings:
    pass
    # -- replace with request to embedding api
    # embeddings = self.__embedding_client.embed_documents(input)
    # return embeddings
    

class ChromaDB:
  def __init__(self, default_collection="default", embedding_model="openai", distance_function="cosine", use_http_client=False, http_host="localhost", http_port=8000, *args, **kwargs):
    if use_http_client:
      self.__client = chromadb.HttpClient(host=http_host, port=http_port)
    else:
      self.__client = chromadb.PersistentClient(
        path = os.path.join(os.getcwd(), "db") 
      )
    
    self.__ef = ChromaEmbeddingFunction(embedding_model, *args, **kwargs)

    self.__collection = self.__client.get_or_create_collection(
        name=default_collection,
        embedding_function=self.__ef,
        metadata={"hnsw:space": distance_function}
      )

  def delete_collection(self, collection):
    self.__client.delete_collection(name=collection)

  def load_collection(self, collection, distance_function="cosine"):
    self.__collection = self.__client.get_or_create_collection(
          name=collection,
          embedding_function=self.__ef,
          metadata={"hnsw:space": distance_function}
        )
    
  def add(self, chunked_documents: list[ChunkType]):
    documents = [chunk.chunk for chunk in chunked_documents]
    metadatas = [chunk.metadata for chunk in chunked_documents]
    ids = [chunk.id for chunk in chunked_documents]
    embeddings = [chunk.embedding for chunk in chunked_documents]

    self.__collection.add(
      ids=ids,
      embeddings=embeddings,
      documents=documents,
      metadatas=metadatas,
    )


  def query(self, query_embeddings: np.ndarray, n_results=10, where=None, where_document=None):
    results = self.__collection.query(
      query_embeddings=query_embeddings,
      n_results=n_results,
      where=where,
      where_document=where_document
    )
  
    metadatas = results["metadatas"][0]
    docs = results["documents"][0]
    distances = results["distances"][0]
    ids = results["ids"][0]

    return ids, distances, docs, metadatas

  def peek(self):
    return self.__collection.peek()

  def count(self):
    return self.__collection.count()

  def rename_collection(self, new_name: str):
    return self.__collection.modify(name=new_name)
  
  def reset_collection(self):
    return self.__collection.delete(ids=self.__collection.get()['ids'])
    
  def heartbeat(self):
    return self.__client.heartbeat()
    

if __name__ == "__main__":
  pass
