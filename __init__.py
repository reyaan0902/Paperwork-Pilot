"""Tool registry. The agent loop uses TOOLS or run_tool().

    from tools import TOOLS, run_tool
    result = run_tool("drafts", {"body": "Call me on [PHONE_1]"}, resolve)
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
