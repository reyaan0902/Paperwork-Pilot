import { useEffect, useState } from 'react';
import { approveTask, createGoal, getPlan, listPlans, saveDocuments } from '../api';
import ApprovalCard from './ApprovalCard';
import ArtifactPanel from './ArtifactPanel';
import Logo from './Logo';

const EXAMPLES = [
  'I need to renew my passport',
  'I need to apply for a scholarship',
  'I need to get campus Wi-Fi access',
];

const STATUS_TEXT = {
  pending: 'Waiting',
  running: 'Running',
  needs_approval: 'Waiting for your approval',
  done: 'Done',
  failed: 'Failed',
};

const NODE_SYMBOL = { pending: '', running: '…', needs_approval: '!', done: '✓', failed: '×' };

function formatDate(iso) {
  if (!iso) return '';
  const date = new Date(iso.endsWith('Z') ? iso : `${iso}Z`);
  return date.toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
}

function Step({ task, onDecide, busy }) {
  const classes = ['step', `step--${task.status}`];
  if (task.replaced) classes.push('step--replaced');

  return (
    <li className={classes.join(' ')}>
      <span className="step__node" aria-hidden="true">{NODE_SYMBOL[task.status]}</span>
      <div className="step__body">
        <p className="step__title">{task.title}</p>
        <p className="step__meta">
          {task.replaced ? 'Replaced by the agent' : STATUS_TEXT[task.status]}
          {task.added_by_agent && <span className="badge">Added by the agent</span>}
        </p>
        {task.status === 'failed' && !task.replaced && typeof task.result === 'string' && (
          <p className="step__error">{task.result}</p>
        )}
        {task.status === 'needs_approval' && <ApprovalCard task={task} onDecide={onDecide} busy={busy} />}
      </div>
    </li>
  );
}

export default function Dashboard({ user, onLogout }) {
  const [plans, setPlans] = useState([]);
  const [plan, setPlan] = useState(null);
  const [goal, setGoal] = useState('');
  const [siteUrl, setSiteUrl] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const firstName = user.name.split(' ')[0];

  // One place to handle errors: a 401 means the login has ended
  function fail(e) {
    if (e.status === 401) onLogout();
    else setError(e.message);
  }

  async function refreshPlans() {
    try {
      setPlans(await listPlans());
    } catch (e) {
      fail(e);
    }
  }

  useEffect(() => {
    refreshPlans();
  }, []);

  async function openPlan(id) {
    setError('');
    try {
      setPlan(await getPlan(id));
      setGoal('');
    } catch (e) {
      fail(e);
    }
  }

  function newPlan() {
    setPlan(null);
    setGoal('');
    setError('');
  }

  async function startGoal(text) {
    const value = (text ?? goal).trim();
    if (!value || busy) return;
    setGoal(value);
    setBusy(true);
    setError('');
    setPlan(null);
    try {
      setPlan(await createGoal(value, siteUrl));
      refreshPlans();
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  }

  async function decide(taskId, approved, feedback, edits = null) {
    setBusy(true);
    setError('');
    try {
      setPlan(await approveTask(plan.plan_id, taskId, approved, feedback, edits));
      refreshPlans();
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  }

  // Ticking a document saves it, so it is still ticked when you come back
  async function changeHave(list) {
    setPlan((p) => ({ ...p, have_documents: list }));
    try {
      await saveDocuments(plan.plan_id, list);
    } catch (e) {
      fail(e);
    }
  }

  // Tasks the agent replaced are shown greyed out and not counted
  const activeTasks = plan ? plan.tasks.filter((t) => !t.replaced) : [];
  const doneCount = activeTasks.filter((t) => t.status === 'done').length;
  const allDone = activeTasks.length > 0 && doneCount === activeTasks.length;
  const stuck = activeTasks.some((t) => t.status === 'failed');
  const percent = activeTasks.length ? Math.round((doneCount / activeTasks.length) * 100) : 0;

  return (
    <div className="shell">
      <header className="topbar">
        <Logo light />
        <div className="topbar__user">
          <span className="avatar" aria-hidden="true">{firstName[0]?.toUpperCase()}</span>
          <span className="topbar__name">{user.name}</span>
          <button className="btn btn--bar" type="button" onClick={onLogout}>Log out</button>
        </div>
      </header>

      <div className="workspace">
        <nav className="plans" aria-label="Your plans">
          <button className="btn btn--primary btn--wide" type="button" onClick={newPlan}>New plan</button>
          <h2>Your paperwork</h2>
          {plans.length === 0 ? (
            <p className="plans__empty">Plans you make will be saved here.</p>
          ) : (
            <ul>
              {plans.map((p) => (
                <li key={p.plan_id}>
                  <button
                    type="button"
                    className={`plans__item${plan?.plan_id === p.plan_id ? ' is-open' : ''}`}
                    onClick={() => openPlan(p.plan_id)}
                  >
                    <span className="plans__goal">{p.goal}</span>
                    <span className="plans__meta">
                      {p.done} of {p.total} steps · {formatDate(p.updated_at)}
                    </span>
                    {p.waiting && <span className="badge badge--ask">Needs your OK</span>}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </nav>

        <main className="agent">
          <header className="agent__header">
            <h1>Hi {firstName}, what do you need to get done?</h1>
            <p>Describe it in your own words. The agent plans the steps and asks before anything important.</p>
          </header>

          <form className="goal" onSubmit={(e) => { e.preventDefault(); startGoal(); }}>
            <label htmlFor="goal" className="sr-only">Your goal</label>
            <div className="goal__row">
              <input
                id="goal"
                type="text"
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="For example: I need to renew my passport"
                disabled={busy}
              />
              <button className="btn btn--primary" type="submit" disabled={busy || !goal.trim()}>Make a plan</button>
            </div>
            <details className="goal__site">
              <summary>Add the registration website (optional)</summary>
              <input
                type="text"
                value={siteUrl}
                onChange={(e) => setSiteUrl(e.target.value)}
                placeholder="https://example.gov.in/register"
                aria-label="Registration website"
                disabled={busy}
              />
            </details>
            <div className="goal__examples">
              {EXAMPLES.map((example) => (
                <button key={example} type="button" className="chip" disabled={busy} onClick={() => startGoal(example)}>
                  {example}
                </button>
              ))}
            </div>
          </form>

          {error && <p className="notice notice--error" role="alert">{error}</p>}
          {busy && <p className="notice" role="status">The agent is working. This can take a few seconds.</p>}

          {plan && (
            <section className="plan" aria-label="Plan">
              <div className="plan__top">
                <h2>{plan.goal}</h2>
                <p>{doneCount} of {activeTasks.length} steps done</p>
              </div>
              <div className="progress" aria-hidden="true">
                <div className="progress__bar" style={{ width: `${percent}%` }} />
              </div>
              {plan.replans > 0 && (
                <p className="plan__note">The agent changed the plan {plan.replans} {plan.replans === 1 ? 'time' : 'times'} after your feedback.</p>
              )}

              <ol className="route">
                {plan.tasks.map((task) => <Step key={task.id} task={task} onDecide={decide} busy={busy} />)}
              </ol>

              {allDone && <p className="notice notice--ok">All steps are done. Everything is saved in your folder.</p>}
              {stuck && (
                <p className="notice notice--error">
                  A step failed and the agent has no re-plans left. Try rewording your goal or starting a new plan.
                </p>
              )}
            </section>
          )}
        </main>

        <ArtifactPanel plan={plan} onHaveChange={changeHave} />
      </div>
    </div>
  );
}
