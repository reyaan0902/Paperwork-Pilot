import { useEffect, useState } from 'react';
import { fetchMe, getToken, setToken, logout } from './api';
import AuthScreen from './components/AuthScreen';
import Dashboard from './components/Dashboard';
import './App.css';

// Decides what to show: the login screen or the dashboard.
export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(Boolean(getToken()));

  // If a token is saved, ask the backend who it belongs to
  useEffect(() => {
    if (!getToken()) return;
    fetchMe()
      .then(setUser)
      .catch((e) => {
        if (e.status === 401) setToken(null); // saved login is no longer valid
      })
      .finally(() => setChecking(false));
  }, []);

  function handleAuth({ token, user: signedIn }) {
    setToken(token);
    setUser(signedIn);
  }

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // logging out locally is enough
    }
    setToken(null);
    setUser(null);
  }

  if (checking) return <p className="boot" role="status">Loading your account…</p>;
  if (!user) return <AuthScreen onAuth={handleAuth} />;

  return (
    <>
      <Dashboard user={user} onLogout={handleLogout} />
    </>
  );
}