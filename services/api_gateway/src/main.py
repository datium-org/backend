from fastapi import FastAPI, File, UploadFile
from typing import Annotated

app = FastAPI()


@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
  return {"file_size": len(file)}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
  contents = await file.read()
  print(contents)
  return {"filename": file.filename}

@app.get("/")
async def root():
  return {"message": "Hello World"}