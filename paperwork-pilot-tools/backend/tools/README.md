# backend/tools/

Actions the agent can run. Owner: Person 3 (Tools).

| Tool | File | Needs real values? | What it does |
|------|------|--------------------|--------------|
| `search` | `search.py` | No | Returns required fields, documents and steps for a workflow from `backend/data/workflows/<workflow>.json` |
| `checklist` | `checklist.py` | No | Marks each required document as have/missing (names only, never contents) |
| `drafts` | `drafts.py` | Yes, local only | Fills placeholders like `[PHONE_1]` into an email/form draft after the LLM step |
| `reminders` | `reminders.py` | No | Creates a reminder (title + due date); rejects personal data |

## Usage
```python
from tools import TOOLS, TOOL_SPECS, run_tool

result = run_tool("drafts", {"subject": "Hi", "body": "Call me on [PHONE_1]"}, resolve)
```

`resolve(text) -> text` is supplied by the gateway/agent and swaps placeholders for real values.

## Result format
```python
{"status": "ok" | "error", "output": ..., "masked_output": ..., "fields_used": [...]}
```
- `output` may contain real values: keep it local.
- `masked_output` is the only version that may go back to the LLM.
- `fields_used` feeds the dashboard audit log.

## Workflow JSON keys expected by `search`
`required_fields`, `required_documents`, `steps`

## Tests
From `backend/`: `pytest tools`
