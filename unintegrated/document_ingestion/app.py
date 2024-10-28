from fastapi import FastAPI, File, UploadFile
from typing import Annotated
import uvicorn

app = FastAPI()

@app.post("/callback")
async def create_upload_file(file: UploadFile):
  contents = await file.read()
  print(contents)
  return {"filename": file.filename}

@app.get("/")
async def root():
  return {"message": "Hello World"}

if __name__ == "__main__":
  uvicorn.run(app, host="localhost", port=8080)