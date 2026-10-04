"""Tool registry (Person 3).

    from tools import TOOLS, TOOL_SPECS, run_tool
    result = run_tool("drafts", {"body": "Call me on [PHONE_1]"}, resolve)

Every tool: run(args: dict, resolve: Callable[[str], str]) -> dict
    {"status": "ok" | "error", "output": ..., "masked_output": ..., "fields_used": [...]}
- output         may contain real values; keep it local
- masked_output  the only version that may be sent back to the LLM
- fields_used    placeholders touched; feeds the dashboard
"""
from . import checklist, drafts, reminders, search

_MODULES = (search, checklist, drafts, reminders)

# name -> run function
TOOLS = {m.SPEC["name"]: m.run for m in _MODULES}

# name -> spec (lets the gateway see what each tool needs)
TOOL_SPECS = {m.SPEC["name"]: m.SPEC for m in _MODULES}


def run_tool(name: str, args: dict, resolve) -> dict:
    fn = TOOLS.get(name)
    if fn is None:
        msg = f"Unknown tool '{name}'."
        return {"status": "error", "output": msg, "masked_output": msg, "fields_used": []}
    return fn(args, resolve)
