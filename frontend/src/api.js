// Talks to the FastAPI backend (backend/main.py).
// Uses relative paths in production on Vercel, or localhost in development.
const API_BASE = import.meta.env.VITE_API_URL !== undefined 
  ? import.meta.env.VITE_API_URL 
  : (import.meta.env.PROD ? '' : 'http://127.0.0.1:8000');

const TOKEN_KEY = 'paperwork_pilot_token';

// The login token lives in the browser so you stay logged in after a refresh
export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token) =>
  token ? localStorage.setItem(TOKEN_KEY, token) : localStorage.removeItem(TOKEN_KEY);

async function request(path, options = {}) {
  const token = getToken();
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  } catch {
    throw new Error('Cannot reach the server. Check that the backend is running.');
  }

  if (!response.ok) {
    // FastAPI sends errors as { "detail": "..." }
    let message = `Server error (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') message = body.detail;
    } catch {
      // keep the default message
    }
    const error = new Error(message);
    error.status = response.status; // 401 means "log in again"
    throw error;
  }
  return response.json();
}

const post = (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) });

// ----- accounts -----
export const signup = (name, email, password) => post('/auth/signup', { name, email, password });
export const login = (email, password) => post('/auth/login', { email, password });
export const fetchMe = () => request('/auth/me');
export const logout = () => post('/auth/logout', {});

// ----- plans -----
export const listPlans = () => request('/plans');
export const createGoal = (goal, siteUrl = '') => post('/goals', { goal, site_url: siteUrl });
export const getPlan = (planId) => request(`/plans/${planId}`);
export const approveTask = (planId, taskId, approved, feedback = '', edits = null) =>
  post(`/plans/${planId}/tasks/${taskId}/approve`, { approved, feedback, edits });
export const saveDocuments = (planId, have) => post(`/plans/${planId}/documents`, { have });
