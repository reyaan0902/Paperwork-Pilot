from backend.tools import run_tool, list_specs

VALUES = {"[PHONE_1]": "9876543210", "[FULL_NAME_1]": "Test User"}


def resolve(text: str) -> str:
    for placeholder, real in VALUES.items():
        text = text.replace(placeholder, real)
    return text


def test_draft_email_fills_locally_and_masks_for_llm():
    res = run_tool("draft_email",
                   {"subject": "Hi", "body": "I am [FULL_NAME_1], call [PHONE_1]"}, resolve)
    assert res["status"] == "ok"
    assert "9876543210" in res["output"]["body"]
    assert "9876543210" not in str(res["masked_output"])
    assert res["fields_used"] == ["[FULL_NAME_1]", "[PHONE_1]"]


def test_reminder_rejects_personal_data():
    res = run_tool("reminder", {"title": "Call 9876543210", "due_date": "2026-11-01"}, resolve)
    assert res["status"] == "error"


def test_reminder_ok():
    res = run_tool("reminder", {"title": "Submit form", "due_date": "2026-11-01"}, resolve)
    assert res["status"] == "ok"


def test_unknown_tool():
    assert run_tool("nope", {}, resolve)["status"] == "error"


def test_specs_listed():
    assert {s["name"] for s in list_specs()} == {
        "requirements_search", "document_checklist", "draft_email", "reminder"}
