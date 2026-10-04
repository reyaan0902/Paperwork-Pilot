import { useState } from 'react';

// Shown under a step that is waiting for the human.
// The draft is editable, like an email. Nothing runs until the person clicks a button.
export default function ApprovalCard({ task, onDecide, busy }) {
  const [feedback, setFeedback] = useState('');
  const [mail, setMail] = useState(task.preview || null); // { to, subject, body }
  const edit = (key) => (e) => setMail({ ...mail, [key]: e.target.value });

  return (
    <section className="checkpoint" aria-label="Approval needed">
      <span className="stamp">Needs your OK</span>
      <h3>Review before the agent continues</h3>
      <p>Nothing happens until you decide.</p>

      {mail && (
        <>
          <div className="mail">
            <label className="mail__row">
              <span>To</span>
              <input value={mail.to || ''} onChange={edit('to')} placeholder="Add the recipient's email" disabled={busy} />
            </label>
            <label className="mail__row">
              <span>Subject</span>
              <input value={mail.subject} onChange={edit('subject')} disabled={busy} />
            </label>
            <label className="sr-only" htmlFor={`body-${task.id}`}>Message</label>
            <textarea id={`body-${task.id}`} value={mail.body} onChange={edit('body')} disabled={busy} />
          </div>
          <p className="mail__hint">You can edit anything above. Text in [BRACKETS] is a personal detail to fill in.</p>
        </>
      )}

      <label className="field">
        <span>Want a different approach? Tell the agent (optional)</span>
        <input
          type="text"
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="For example: skip the email, I will go in person"
          disabled={busy}
        />
      </label>

      <div className="actions">
        <button
          className="btn btn--primary"
          type="button"
          disabled={busy}
          onClick={() => onDecide(task.id, true, '', mail)}
        >
          Approve and continue
        </button>
        <button className="btn btn--ghost" type="button" disabled={busy} onClick={() => onDecide(task.id, false, feedback)}>
          Reject and re-plan
        </button>
      </div>
    </section>
  );
}
