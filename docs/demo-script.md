# Demo Script: Paperwork Pilot

## 1. The Hook (0:00 - 0:30)
- "Bureaucratic tasks like passport renewal, scholarships, and campus Wi-Fi access drown users in messy requirements, confusing forms, and strict deadlines."
- "Fully automated bots are dangerous when handling legal paperwork. Paperwork Pilot balances autonomy with safety through Human-in-the-Loop (HITL) checkpoints."

## 2. Live Execution Walkthrough (0:30 - 2:00)
1. **Goal Input:** Enter: `"I need to renew my passport."`
2. **Dynamic Task Plan:** The agent loads the workflow schema into structured tasks (`t1` to `t4`).
3. **Autonomous Execution:**
   - `t1` (Search Requirements) runs in the background -> Status changes to `done`.
   - `t2` (Make Checklist) compiles required proofs -> Status changes to `done`.
4. **Safety Interception (HITL Gate):**
   - The loop stops at `t3` (Draft Email / Application).
   - Status switches to `needs_approval`. The UI surfaces an Approval Card with drafted contents.
5. **Human Sign-Off:**
   - The user inspects and clicks `Approve`.
   - Decision is permanently logged to `approval_log.json`.
   - The agent triggers `t4` (Set Reminder) and finishes the flow -> Status: `done`.

## 3. Reliability & Architecture (2:00 - 2:30)
- Decoupled contract architecture: UI, Agent Loop, Modular Tools, and Schema Data Storage.
- Safe-by-default execution: Zero unapproved outbound requests or submissions.
