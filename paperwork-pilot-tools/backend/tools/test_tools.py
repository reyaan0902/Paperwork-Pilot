import json

from tools import TOOLS, TOOL_SPECS, run_tool, search

VALUES = {"[PHONE_1]": "9876543210", "[FULL_NAME_1]": "Test User"}


def resolve(text: str) -> str:
    for placeholder, real in VALUES.items():
        text = text.replace(placeholder, real)
    return text


def test_registry_has_all_tools():
    assert set(TOOLS) == {"search", "checklist", "drafts", "reminders"}
    assert set(TOOL_SPECS) == set(TOOLS)


def test_drafts_fills_locally_and_masks_for_llm():
    res = run_tool("drafts", {"subject": "Hi", "body": "I am [FULL_NAME_1], call [PHONE_1]"}, resolve)
    assert res["status"] == "ok"
    assert "9876543210" in res["output"]["body"]
    assert "9876543210" not in str(res["masked_output"])
    assert res["fields_used"] == ["[FULL_NAME_1]", "[PHONE_1]"]


def test_reminders_rejects_personal_data():
    res = run_tool("reminders", {"title": "Call 9876543210", "due_date": "2026-11-01"}, resolve)
    assert res["status"] == "error"


def test_reminders_ok():
    res = run_tool("reminders", {"title": "Submit form", "due_date": "2026-11-01"}, resolve)
    assert res["status"] == "ok"


def test_search_and_checklist(tmp_path, monkeypatch):
    (tmp_path / "demo.json").write_text(json.dumps({
        "required_fields": ["FULL_NAME", "PHONE"],
        "required_documents": ["address proof", "photo"],
        "steps": ["Apply online"],
    }))
    monkeypatch.setattr(search, "WORKFLOW_DIR", tmp_path)

    found = run_tool("search", {"workflow": "demo"}, resolve)
    assert found["status"] == "ok"
    assert found["output"]["required_fields"] == ["FULL_NAME", "PHONE"]

    res = run_tool("checklist", {"workflow": "demo", "available_documents": ["Photo"]}, resolve)
    assert res["output"]["missing"] == ["address proof"]


def test_unknown_tool():
    assert run_tool("nope", {}, resolve)["status"] == "error"
