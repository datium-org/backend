from fastapi import FastAPI, File, UploadFile
from typing import Annotated
import uvicorn

app = FastAPI()

@app.post("/callback")
async def callback():
  return {"callback": "callbacked"}

@app.get("/")
async def root():
  return {"message": "Hello World"}

if __name__ == "__main__":
  uvicorn.run(app, host="localhost", port=8080)