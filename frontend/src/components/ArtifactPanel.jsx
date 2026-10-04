import { useState } from 'react';

// The "folder" on the right. It collects what the agent produced:
// registration shortcut, requirements, documents, drafts and reminders.

const isObject = (value) => value !== null && typeof value === 'object';

// ----- calendar helpers (all-day event on the chosen date) -----
const pad = (n) => String(n).padStart(2, '0');
const compact = (iso) => iso.replaceAll('-', '');

function nextDay(iso) {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + 1);
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`;
}

const googleUrl = (title, date) =>
  `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${compact(date)}/${nextDay(date)}`;

function downloadIcs(title, date) {
  const stamp = new Date().toISOString().replace(/[-:]|\.\d{3}/g, '');
  const lines = [
    'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Paperwork Pilot//EN', 'BEGIN:VEVENT',
    `UID:${Date.now()}@paperworkpilot`, `DTSTAMP:${stamp}`,
    `DTSTART;VALUE=DATE:${compact(date)}`, `DTEND;VALUE=DATE:${nextDay(date)}`,
    `SUMMARY:${title}`, 'END:VEVENT', 'END:VCALENDAR',
  ];
  const url = URL.createObjectURL(new Blob([lines.join('\r\n')], { type: 'text/calendar' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'reminder.ics';
  link.click();
  URL.revokeObjectURL(url);
}

function Section({ title, children }) {
  return (
    <section className="folder__section">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

const Note = ({ children }) => <p className="folder__note">{children}</p>;

// ----- registration shortcut -----
function Registration({ url, fields }) {
  const [values, setValues] = useState({}); // stays in this browser tab only
  const [copied, setCopied] = useState('');

  async function copy(field) {
    try {
      await navigator.clipboard.writeText(values[field] || '');
      setCopied(field);
      setTimeout(() => setCopied(''), 1500);
    } catch {
      // clipboard not allowed: the person can still select the text
    }
  }

  return (
    <Section title="Registration">
      <a className="btn btn--primary btn--small" href={url} target="_blank" rel="noopener noreferrer">
        Open the website
      </a>
      <Note>You press the final submit button yourself, so nothing is sent without you.</Note>
      {fields.length > 0 && (
        <>
          <p className="folder__label">Your details, ready to copy</p>
          <Note>What you type here stays in this browser tab. It is never sent to the agent.</Note>
          {fields.map((field) => (
            <div className="copyrow" key={field}>
              <label>
                <span>{field}</span>
                <input
                  value={values[field] || ''}
                  onChange={(e) => setValues({ ...values, [field]: e.target.value })}
                />
              </label>
              <button className="btn btn--ghost btn--small" type="button" disabled={!values[field]} onClick={() => copy(field)}>
                {copied === field ? 'Copied' : 'Copy'}
              </button>
            </div>
          ))}
        </>
      )}
    </Section>
  );
}

// ----- documents with checkboxes -----
function Documents({ items, have, onHaveChange }) {
  const isHave = (item) => item.status === 'have' || have.includes(item.document);
  const ready = items.filter(isHave).length;
  const toggle = (doc) => onHaveChange(have.includes(doc) ? have.filter((d) => d !== doc) : [...have, doc]);

  return (
    <>
      <Note>{ready} of {items.length} documents ready. Tick each one you already have.</Note>
      <ul className="checklist">
        {items.map((item) => (
          <li key={item.document}>
            <label className={`check${isHave(item) ? ' is-have' : ''}`}>
              <input type="checkbox" checked={isHave(item)} disabled={item.status === 'have'} onChange={() => toggle(item.document)} />
              <span>{item.document}</span>
            </label>
          </li>
        ))}
      </ul>
      {items.length > 0 && ready === items.length && <p className="notice notice--ok">You have everything you need.</p>}
    </>
  );
}

// ----- one reminder, with calendar buttons -----
function Reminder({ title, dueDate }) {
  const [date, setDate] = useState(dueDate);
  return (
    <li className="reminder">
      <p className="reminder__title">{title}</p>
      <label className="reminder__date">
        Date
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </label>
      <div className="reminder__actions">
        <a
          className={`btn btn--ghost btn--small${date ? '' : ' is-off'}`}
          href={date ? googleUrl(title, date) : undefined}
          target="_blank"
          rel="noopener noreferrer"
        >
          Add to Google Calendar
        </a>
        <button className="btn btn--ghost btn--small" type="button" disabled={!date} onClick={() => downloadIcs(title, date)}>
          Download .ics
        </button>
      </div>
    </li>
  );
}

export default function ArtifactPanel({ plan, onHaveChange }) {
  const tasks = plan ? plan.tasks.filter((t) => !t.replaced) : [];
  const have = plan?.have_documents || [];
  const withTool = (tool) => tasks.filter((t) => t.tool === tool);

  const requirements = withTool('search_requirements').filter((t) => t.status === 'done' && isObject(t.result));
  const checklists = withTool('make_checklist').filter((t) => t.status === 'done' && isObject(t.result));
  const drafts = withTool('draft_email').filter((t) => t.status === 'done' || (t.status === 'needs_approval' && t.preview));
  const reminders = withTool('set_reminder').filter((t) => t.status === 'done' && isObject(t.result));

  const fields = requirements.flatMap((t) => t.result.required_fields || []);
  const empty = !plan?.site_url && !requirements.length && !checklists.length && !drafts.length && !reminders.length;

  return (
    <aside className="folder" aria-label="Your paperwork folder">
      <h2>Your paperwork folder</h2>

      {empty && <Note>Requirements, documents, drafts and reminders appear here as the agent works.</Note>}

      {plan?.site_url && <Registration url={plan.site_url} fields={fields} key={plan.plan_id} />}

      {requirements.length > 0 && (
        <Section title="Requirements">
          {requirements.map((task) => (
            <div key={task.id}>
              {task.result.required_documents?.length > 0 && (
                <>
                  <p className="folder__label">Documents</p>
                  <ul>{task.result.required_documents.map((d) => <li key={d}>{d}</li>)}</ul>
                </>
              )}
              {task.result.required_fields?.length > 0 && (
                <>
                  <p className="folder__label">Details you will need</p>
                  <ul>{task.result.required_fields.map((f) => <li key={f}>{f}</li>)}</ul>
                </>
              )}
              {task.result.steps?.length > 0 && (
                <>
                  <p className="folder__label">Steps</p>
                  <ol>{task.result.steps.map((s) => <li key={s}>{s}</li>)}</ol>
                </>
              )}
            </div>
          ))}
        </Section>
      )}

      {checklists.map((task) => (
        <Section title="Documents" key={task.id}>
          {task.result.checklist?.length ? (
            <Documents items={task.result.checklist} have={have} onHaveChange={onHaveChange} />
          ) : (
            <Note>No documents are listed for this process yet.</Note>
          )}
        </Section>
      ))}

      {drafts.length > 0 && (
        <Section title="Drafts">
          {drafts.map((task) => {
            const approved = task.status === 'done' && isObject(task.result);
            const draft = approved ? { ...task.result, to: task.preview?.to || '' } : task.preview;
            const mailto = `mailto:${draft.to}?subject=${encodeURIComponent(draft.subject)}&body=${encodeURIComponent(draft.body)}`;
            return (
              <div key={task.id} className="paper">
                <p className="paper__state">{approved ? 'Approved' : 'Waiting for your approval'}</p>
                {draft.to && <p className="paper__to">To: {draft.to}</p>}
                <p className="paper__subject">{draft.subject}</p>
                <pre className="paper__body">{draft.body}</pre>
                {approved && (
                  <div className="reminder__actions">
                    <a className="btn btn--primary btn--small" href={mailto}>Open in my email app</a>
                    <button className="btn btn--ghost btn--small" type="button" onClick={() => navigator.clipboard?.writeText(`${draft.subject}\n\n${draft.body}`)}>
                      Copy text
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </Section>
      )}

      {reminders.length > 0 && (
        <Section title="Reminders">
          <ul className="reminders">
            {reminders.map((task) => (
              <Reminder key={task.id} title={task.result.title} dueDate={task.result.due_date} />
            ))}
          </ul>
        </Section>
      )}
    </aside>
  );
}
