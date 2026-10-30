"""Tiny hello crew: one agent, one task, local model through the LiteLLM front door."""
from __future__ import annotations

import os

from crewai import Agent, Crew, Task
from crewai.llm import LLM


def run_hello() -> str:
    llm = LLM(
        model=os.environ.get("AD_LLM_MODEL", "long-context-local"),
        base_url=os.environ.get("AD_LLM_BASE", "http://$RIG_HOST:4000/v1"),
        api_key=os.environ.get("AD_LLM_KEY", "none"),
    )
    agent = Agent(
        role="Proof Runner",
        goal="Reply with exactly HELLO-AGENT-CREWAI-OK",
        backstory="Deterministic proof agent. No extra words.",
        llm=llm,
    )
    task = Task(
        description="Say the exact required reply token and nothing else.",
        expected_output="HELLO-AGENT-CREWAI-OK",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], process="sequential")
    return str(crew.kickoff().raw)
