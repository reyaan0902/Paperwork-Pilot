import { useState } from 'react';
import { login, signup } from '../api';
import Logo from './Logo';

const PREVIEW = [
  { text: 'Find what a passport renewal needs', state: 'done' },
  { text: 'Check your documents', state: 'done' },
  { text: 'Draft the appointment email', state: 'ask' },
  { text: 'Set a reminder for the visit', state: 'wait' },
];

export default function AuthScreen({ onAuth }) {
  const [mode, setMode] = useState('login'); // 'login' or 'signup'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const isSignup = mode === 'signup';

  function switchMode(next) {
    setMode(next);
    setError('');
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      onAuth(isSignup ? await signup(name, email, password) : await login(email, password));
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      <section className="auth__brand">
        <Logo light />
        <h1>Paperwork, one step at a time.</h1>
        <p>
          Say what you need to get done. Paperwork Pilot makes the plan, does the work, and stops to ask you
          before anything important happens.
        </p>

        <div className="preview" aria-hidden="true">
          <p className="preview__goal">I need to renew my passport</p>
          <ol>
            {PREVIEW.map((step) => (
              <li key={step.text} className={`preview__step preview__step--${step.state}`}>
                <span className="preview__dot">{step.state === 'done' ? '✓' : step.state === 'ask' ? '!' : ''}</span>
                <span>{step.text}</span>
                {step.state === 'ask' && <span className="stamp stamp--small">Needs your OK</span>}
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="auth__panel">
        <form className="auth__form" onSubmit={submit}>
          <h2>{isSignup ? 'Create your account' : 'Welcome back'}</h2>
          <p className="auth__sub">
            {isSignup ? 'Your plans and drafts stay private to you.' : 'Log in to continue with your paperwork.'}
          </p>

          <div className="tabs" role="tablist">
            <button type="button" role="tab" aria-selected={!isSignup} className={!isSignup ? 'is-on' : ''} onClick={() => switchMode('login')}>
              Log in
            </button>
            <button type="button" role="tab" aria-selected={isSignup} className={isSignup ? 'is-on' : ''} onClick={() => switchMode('signup')}>
              Sign up
            </button>
          </div>

          {isSignup && (
            <label className="field">
              <span>Your name</span>
              <input value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" required />
            </label>
          )}
          <label className="field">
            <span>Email</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={isSignup ? 'new-password' : 'current-password'}
              minLength={isSignup ? 6 : undefined}
              required
            />
            {isSignup && <small>At least 6 characters</small>}
          </label>

          {error && <p className="notice notice--error" role="alert">{error}</p>}

          <button className="btn btn--primary btn--wide" type="submit" disabled={busy}>
            {busy ? 'Please wait…' : isSignup ? 'Create account' : 'Log in'}
          </button>
        </form>
      </section>
    </div>
  );
}
