"""Tool: document checklist.

Compares a workflow's required documents with the documents the user has.
Works on document names only (e.g. "address proof"), never document contents.

args: {"workflow": "passport", "available_documents": ["photo", "birth certificate"]}
"""
from . import search

SPEC = {
    "name": "checklist",
    "description": "Mark each required document as have/missing.",
    "needs_real_values": False,
}


def run(args: dict, resolve=None) -> dict:
    found = search.run(args)
    if found["status"] != "ok":
        return found

    have = {str(d).strip().lower() for d in args.get("available_documents", [])}
    items = [
        {"document": doc, "status": "have" if str(doc).lower() in have else "missing"}
        for doc in found["output"]["required_documents"]
    ]
    result = {
        "workflow": found["output"]["workflow"],
        "checklist": items,
        "missing": [i["document"] for i in items if i["status"] == "missing"],
    }
    return {"status": "ok", "output": result, "masked_output": result, "fields_used": []}
