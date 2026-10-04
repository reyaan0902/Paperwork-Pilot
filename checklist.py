"""Tool: document checklist.

Compares a workflow's required documents with the ones the user has.
Works on document names only (e.g. "address proof"), never document contents.
"""
from ._common import ok
from . import search

SPEC = {
    "name": "checklist",
    "description": "Mark each required document as have/missing.",
    "needs_real_values": False,
}


def run(args: dict, resolve=None) -> dict:
    found = search.run({"workflow": args.get("workflow", "")})
    if found["status"] != "ok":
        return found

    have = {d.strip().lower() for d in args.get("available_documents", [])}
    items = [
        {"document": doc, "status": "have" if doc.lower() in have else "missing"}
        for doc in found["output"]["required_documents"]
    ]
    return ok({"checklist": items, "missing": [i["document"] for i in items if i["status"] == "missing"]})
