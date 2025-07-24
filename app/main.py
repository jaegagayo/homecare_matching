from typing import Union

from fastapi import FastAPI

app = FastAPI()

@app.get("/health-check")
def health():
    return {"status": "ok"}