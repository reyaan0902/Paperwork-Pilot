"""Tool: compare required documents with what the user has.

Works on document names only (e.g. "address proof"), never document contents.
"""
from .base import ok, error
from .requirements_search import run as search_requirements

TOOL_SPEC = {
    "name": "document_checklist",
    "description": "Mark each required document as have/missing.",
    "required_fields": [],
    "optional_fields": [],
    "needs_real_values": False,
}


def run(args: dict, resolve=None) -> dict:
    found = search_requirements({"workflow": args.get("workflow", "")})
    if found["status"] != "ok":
        return found

    have = {d.strip().lower() for d in args.get("available_documents", [])}
    checklist = [
        {"document": doc, "status": "have" if doc.lower() in have else "missing"}
        for doc in found["output"]["required_documents"]
    ]
    missing = [c["document"] for c in checklist if c["status"] == "missing"]
    return ok({"checklist": checklist, "missing": missing})
