# backend/tools/

Actions the agent can run. Owned by: Tools (person 3).

## Tools
| Tool | Needs real values? | What it does |
|------|--------------------|--------------|
| `requirements_search` | No | Returns required fields/documents/steps for a workflow template |
| `document_checklist` | No | Marks required documents as have/missing (names only) |
| `draft_email` | Yes (local only) | Fills placeholders like `[PHONE_1]` into a draft after the LLM step |
| `reminder` | No | Creates a reminder; rejects personal data |

## Contract
```python
run_tool(name: str, args: dict, resolve: Callable[[str], str]) -> dict
# {"status", "output", "masked_output", "fields_used"}
```
- `output` may contain real values: keep it local.
- `masked_output` is the only thing that may go back to the LLM.
- `fields_used` feeds the dashboard audit log.
- `list_specs()` lets the gateway see each tool's data needs.

## Workflow templates
`requirements_search` reads `backend/data/templates/<workflow>.json` with keys
`required_fields`, `required_documents`, `steps`.

## Run tests
From the repo root: `pip install pytest` then `pytest backend/tools/tests`
