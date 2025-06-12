from fastapi import FastAPI
from routers import parser_router, matcher_router, skills_router

app = FastAPI()

app.include_router(parser_router, prefix="/parser", tags=["parser"])
app.include_router(matcher_router, prefix="/matcher", tags=["matcher"])
# app.include_router(skills_router, prefix="/skills", tags=["skills"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8011)
