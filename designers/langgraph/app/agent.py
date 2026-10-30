"""Tiny hello-agent graph: one LLM call to the local LiteLLM front door."""
from __future__ import annotations

import os
from typing import Literal, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def call_llm(state: State) -> State:
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=os.environ.get("AD_LLM_MODEL", "long-context-local"),
        base_url=os.environ.get("AD_LLM_BASE", "http://192.168.68.53:4000/v1"),
        api_key=os.environ.get("AD_LLM_KEY", "none"),
        max_tokens=1024,
        temperature=0,
    )
    out = llm.invoke(
        [
            SystemMessage("You are a proof runner. Reply with exactly: HELLO-AGENT-LANGGRAPH-OK"),
            *state["messages"],
        ]
    )
    return {"messages": [out]}


builder = StateGraph(State)
builder.add_node("call_llm", call_llm)
builder.add_edge(START, "call_llm")
builder.add_edge("call_llm", END)

graph = builder.compile()
