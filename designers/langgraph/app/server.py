"""FastAPI wrapper around the MIT LangGraph hello-agent graph."""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from agent import graph

app = FastAPI(title="RIG LangGraph hello-agent (MIT core)")


class Msg(BaseModel):
    msg: str = "hello"


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/run")
def run(body: Msg) -> dict:
    out = graph.invoke({"messages": [("user", body.msg)]})
    text = out["messages"][-1].content
    return {"reply": text}
