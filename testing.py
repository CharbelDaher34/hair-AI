from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn
app=FastAPI()

@app.get("/")
async def root(pydantic_model:BaseModel):
    print(pydantic_model)
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80010)