# Shared contract

## Task
```json
{
  "id": "t1",
  "title": "Collect required documents",
  "status": "pending",
  "tool": "make_checklist",
  "needs_approval": false,
  "result": null
}
```
`status` is one of: `pending`, `running`, `needs_approval`, `done`, `failed`.

Extra optional fields the agent may add:
- `replaced: true`: the agent replaced this task with new ones
- `added_by_agent: true`: the task was added while re-planning
- `preview`: `{subject, body}` draft shown to the user before approval
- `fields_used`: placeholders a tool touched

## Endpoints
| Endpoint | Body | Returns |
|---|---|---|
| `POST /goals` | `{"goal": "..."}` | the plan: `{plan_id, goal, replans, tasks}` |
| `GET /plans/{plan_id}` | none | the plan |
| `POST /plans/{plan_id}/tasks/{task_id}/approve` | `{"approved": true, "feedback": ""}` | the updated plan |

## Tool names
The plan uses `search_requirements`, `make_checklist`, `draft_email`, `set_reminder`.
`backend/agent/loop.py` maps them to Person 3's tools: `search`, `checklist`, `drafts`, `reminders`.

## Accounts (added)
| Endpoint | Body | Returns |
|---|---|---|
| `POST /auth/signup` | `{"name", "email", "password"}` | `{token, user}` |
| `POST /auth/login` | `{"email", "password"}` | `{token, user}` |
| `GET /auth/me` | none | the user |
| `POST /auth/logout` | none | `{ok: true}` |
| `GET /plans` | none | short summaries of the user's own plans |

Every `/plans` and `/goals` request must send `Authorization: Bearer <token>`.
Each user can only open their own plans.
