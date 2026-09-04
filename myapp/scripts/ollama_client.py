"""Thin wrapper around Ollama's /api/chat for the two-turn harness."""
import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:9b"

# Held fixed across all scenarios per EXECUTION_SPEC.md §2. Ollama accepted
# an explicit seed without erroring in the smoke test; whether the llama.cpp
# backend gives bit-exact reproducibility from it wasn't separately verified
# (not worth the time per the spec's own 15-minute cap) - noted as a
# limitation in the write-up rather than relied upon.
GEN_PARAMS = {"temperature": 0.7, "seed": 42}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file, overwriting its previous contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "New full file content"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the current contents of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"},
                },
                "required": ["path"],
            },
        },
    },
]


def call_chat(messages, tools=None):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "think": True,
        "options": GEN_PARAMS,
    }
    if tools is not None:
        payload["tools"] = tools

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # generation is slow (~8-9 tok/s observed) on this machine; give scenarios
    # with long thinking traces plenty of room before timing out.
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))
