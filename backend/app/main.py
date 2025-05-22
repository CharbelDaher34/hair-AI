from fastapi import FastAPI
from core.database import create_db_and_tables, check_db_tables
from contextlib import asynccontextmanager
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    all_exist, missing_tables = check_db_tables()
    if not all_exist:
        print("Creating database tables...")
        create_db_and_tables()
    else:
        print(f"Database already exists. Missing tables: {missing_tables}")
    
    yield  # Control passes to the application here

    # Shutdown logic (optional)
    # e.g., cleanup, close DB connections
# Add your routers here, for example:
# from .api.v1.endpoints import some_router
# app.include_router(some_router, prefix="/api/v1")
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8017)