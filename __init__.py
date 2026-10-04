"""Tool registry. The agent calls run_tool(name, args, resolve)."""
from . import draft_email, document_checklist, reminder, requirements_search

_MODULES = (requirements_search, document_checklist, draft_email, reminder)

TOOLS = {m.TOOL_SPEC["name"]: m for m in _MODULES}


def list_specs() -> list[dict]:
    """Specs for the gateway: which tools exist and what data they need."""
    return [m.TOOL_SPEC for m in _MODULES]


def run_tool(name: str, args: dict, resolve) -> dict:
    tool = TOOLS.get(name)
    if tool is None:
        return {"status": "error", "output": f"Unknown tool '{name}'.",
                "masked_output": f"Unknown tool '{name}'.", "fields_used": []}
    return tool.run(args, resolve)
