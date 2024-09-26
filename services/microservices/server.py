from services.microservices.scraper.router.router import router as scraper_router

import uvicorn
import logging

from fastapi import FastAPI

logging.basicConfig(level=logging.DEBUG, filename='logs/std.log', filemode='w', format='%(asctime)s: %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(name="server")


app = FastAPI()

# Include the router with a prefix
app.include_router(scraper_router, prefix="/api/service/scraper")

def serve(port=50051):
  uvicorn.run("server:app", host="127.0.0.1", port=port, reload=True, reload_dirs=["interactions/db_service", "interactions/intelligence_service"])
  logger.info(f"Server started, listening on {port}")

if __name__ == '__main__':
  serve(port=50051)