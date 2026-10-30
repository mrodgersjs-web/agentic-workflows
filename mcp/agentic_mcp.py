#!/usr/bin/env python3
"""Agentic designers MCP shim (Aside). One file, six servers via AD_TOOL env.

Stdio JSON-RPC 2.0, newline framing (same contract the Aside jarvis-mcp uses).
Reads the per-tool API key from the macOS keychain at startup; talks plain HTTP
to the self-hosted designers over the tailnet. No third-party deps.
"""
import json
import os
import subprocess
import sys
import urllib.request

BASE_DEFAULTS = {
    "n8n": "http://$RIG_HOST:5678",
    "flowise": "http://$RIG_HOST:3112",
    "dify": "http://$RIG_HOST:8088",
    "trigger": "http://$RIG_HOST:8030",
    "langgraph": "http://$RIG_HOST:2100",
    "crewai": "http://$RIG_HOST:8321",
}
TRIGGER_PROJECT = os.environ.get("AD_TRIGGER_PROJECT", "proj_wqecphayzmxfytidabmr")
FLOWISE_FLOW = os.environ.get("AD_FLOWISE_FLOW", "df3fe622-faab-42df-8c15-291973c4877e")
N8N_WORKFLOW = os.environ.get("AD_N8N_WORKFLOW", "KEe7kKnlLThoYT90")
N8N_WEBHOOK = os.environ.get("AD_N8N_WEBHOOK", "hello-agent")
TOOL = os.environ.get("AD_TOOL", "")


def keychain(service):
    out = subprocess.run(
        ["security", "find-generic-password", "-s", service, "-w"],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("keychain miss: %s" % service)
    return out.stdout.strip()


def base_url(tool):
    return os.environ.get("AD_BASE", BASE_DEFAULTS[tool])


def http(method, url, headers=None, body=None, timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("content-type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode()
    try:
        return r.status, json.loads(raw)
    except ValueError:
        return r.status, raw


def auth_headers():
    if TOOL == "n8n":
        return {"X-N8N-API-KEY": keychain("com.rig.env.N8N_API_KEY")}
    if TOOL == "flowise":
        return {"Authorization": "Bearer " + keychain("com.rig.env.FLOWISE_API_KEY")}
    if TOOL == "dify":
        return {}  # per-call keys
    if TOOL == "trigger":
        return {"Authorization": "Bearer " + keychain("com.rig.env.TRIGGER_PROJECT_KEY")}
    return {}


def call_tool(args):
    b = base_url(TOOL)
    a = auth_headers()
    args = args or {}
    if TOOL == "n8n":
        op = args.get("op", "status")
        if op == "status":
            s, r = http("GET", b + "/healthz", a)
            return "n8n healthz %s" % s
        if op == "list_workflows":
            s, r = http("GET", b + "/api/v1/workflows?active=true", a)
            return json.dumps([{"id": w["id"], "name": w["name"], "active": w["active"]}
                               for w in r.get("data", [])])
        if op == "get_workflow":
            s, r = http("GET", b + "/api/v1/workflows/" + args["id"], a)
            return json.dumps({"name": r.get("name"), "active": r.get("active"),
                               "nodes": [n["name"] for n in r.get("nodes", [])]})
        if op in ("activate", "deactivate"):
            s, r = http("POST", b + "/api/v1/workflows/%s/%s" % (args["id"], op), a)
            return "%s %s -> %s" % (op, args["id"], s)
        if op == "run_hello":
            s, r = http("POST", b + "/webhook/" + N8N_WEBHOOK, a,
                        {"q": args.get("q", "say hello")})
            return json.dumps({"http": s, "response": r})
        if op == "executions":
            s, r = http("GET", b + "/api/v1/executions?limit=%d" % int(args.get("limit", 5)), a)
            return json.dumps([{"id": e["id"], "status": e["status"], "workflow": e["workflowId"]}
                               for e in r.get("data", [])])
        if op == "execution":
            s, r = http("GET", b + "/api/v1/executions/%s?includeData=true" % args["id"], a)
            return json.dumps(r)[:4000]
        raise ValueError("unknown op: %s" % op)
    if TOOL == "flowise":
        op = args.get("op", "status")
        if op == "status":
            s, r = http("GET", b + "/api/v1/settings?type=LICENSE", a)
            return "flowise %s" % json.dumps(r)
        if op == "run":
            s, r = http("POST", b + "/api/v1/prediction/" + args.get("flow_id", FLOWISE_FLOW),
                        a, {"question": args.get("q", "go")})
            return json.dumps(r)[:4000]
        raise ValueError("unknown op: %s" % op)
    if TOOL == "dify":
        op = args.get("op", "status")
        if op == "status":
            s, r = http("GET", b + "/v1/parameters",
                        {"Authorization": "Bearer " + keychain("com.rig.env.DIFY_WORKFLOW_API_KEY")})
            return "dify parameters %s %s" % (s, json.dumps(r)[:200])
        if op == "run_workflow":
            s, r = http("POST", b + "/v1/workflows/run",
                        {"Authorization": "Bearer " + keychain("com.rig.env.DIFY_WORKFLOW_API_KEY")},
                        {"inputs": args.get("inputs", {"proof_input": "say hello"}),
                         "response_mode": "blocking", "user": "aside-mcp"})
            return json.dumps(r)[:4000]
        if op == "chat":
            s, r = http("POST", b + "/v1/chat-messages",
                        {"Authorization": "Bearer " + keychain("com.rig.env.DIFY_CHAT_API_KEY")},
                        {"inputs": {}, "query": args.get("q", "say hello"),
                         "response_mode": "blocking", "user": "aside-mcp"})
            return json.dumps(r)[:4000]
        raise ValueError("unknown op: %s" % op)
    if TOOL == "trigger":
        op = args.get("op", "status")
        if op == "status":
            s, r = http("GET", b + "/api/v1/projects/" + TRIGGER_PROJECT + "/dev", a)
            return "trigger project %s dev-session %s" % (s, json.dumps(r)[:200])
        if op == "trigger":
            s, r = http("POST", b + "/api/v1/tasks/" + args.get("task", "hello-agent") + "/trigger",
                        a, {"payload": args.get("payload", {"q": "say hello"})})
            return json.dumps(r)[:2000]
        if op == "runs":
            s, r = http("GET", b + "/api/v1/runs?limit=%d" % int(args.get("limit", 5)), a)
            return json.dumps(r)[:4000]
        raise ValueError("unknown op: %s" % op)
    if TOOL in ("langgraph", "crewai"):
        op = args.get("op", "status")
        if op == "status":
            s, r = http("GET", b + "/health", a)
            return "%s health %s %s" % (TOOL, s, json.dumps(r)[:120])
        if op == "run":
            s, r = http("POST", b + "/run", a, {"q": args.get("q", "say hello")})
            return json.dumps(r)[:4000]
        raise ValueError("unknown op: %s" % op)
    raise ValueError("AD_TOOL not set / unknown: %r" % TOOL)


OPS = {
    "n8n": ["status", "list_workflows", "get_workflow", "activate", "deactivate",
            "run_hello", "executions", "execution"],
    "flowise": ["status", "run"],
    "dify": ["status", "run_workflow", "chat"],
    "trigger": ["status", "trigger", "runs"],
    "langgraph": ["status", "run"],
    "crewai": ["status", "run"],
}

TOOLS = [{
    "name": "agentic_%s" % (TOOL or "tool"),
    "description": "Control the self-hosted %s designer on rig256gb (tailnet). ops: %s" %
                   (TOOL, ", ".join(OPS.get(TOOL, []))),
    "inputSchema": {
        "type": "object",
        "properties": {
            "args": {
                "type": "object",
                "description": 'op (required; one of %s), plus id/q/flow_id/task/inputs/limit as needed' %
                               ", ".join(OPS.get(TOOL, [])),
            }
        },
        "required": ["args"],
    },
}]

HANDLERS = {"agentic_%s" % (TOOL or "tool"): lambda a: (call_tool(a.get("args")), False)}


def handle(req):
    method = req.get("method")
    rid = req.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "agentic-designers-%s" % TOOL, "version": "1.0.0"}}}
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name")
        handler = HANDLERS.get(name)
        if handler is None:
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32601, "message": "unknown tool: %s" % name}}
        try:
            text, is_error = handler(params.get("args") or {})
        except Exception as e:
            text, is_error = "%s failed: %s" % (name, e), True
        result = {"content": [{"type": "text", "text": text}]}
        if is_error:
            result["isError"] = True
        return {"jsonrpc": "2.0", "id": rid, "result": result}
    if rid is None:
        return None
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": "unknown method: %s" % method}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except ValueError:
            continue
        resp = handle(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
