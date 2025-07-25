from fastapi import FastAPI
from api.matching import router

app = FastAPI(title="Homecare Matching API", version="1.0.0")
app.include_router(router, prefix="/matching", tags=["matching"])

@app.get("/health-check")
def health():
    return {"status": "ok"}