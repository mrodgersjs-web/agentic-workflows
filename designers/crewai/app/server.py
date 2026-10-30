from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from crew import run_hello

app = FastAPI(title="RIG CrewAI hello-crew (self-hosted)")


class Msg(BaseModel):
    msg: str = "hello"


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/run")
def run(body: Msg) -> dict:
    return {"reply": run_hello()}
