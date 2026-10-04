import React, { useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';

export default function Example({ user: appUser }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);
  const [newTitle, setNewTitle] = useState('');
  const [inserting, setInserting] = useState(false);

  const tableName = 'test_items';
  const activeEmail = appUser?.email || appUser?.username || 'guest@example.com';

  async function loadData() {
    setLoading(true);
    setErrorMsg(null);

    try {
      const { data, error: tableError } = await supabase
        .from(tableName)
        .select('*')
        .order('id', { ascending: true });

      if (tableError) {
        throw tableError;
      }

      setItems(data || []);
    } catch (err) {
      console.error('[Supabase Error]:', err);
      setErrorMsg(err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleAddItem(e) {
    e.preventDefault();
    if (!newTitle.trim()) return;

    setInserting(true);
    setErrorMsg(null);

    try {
      const payload = {
        title: newTitle.trim(),
        status: 'pending',
        user_email: activeEmail,
      };

      const { error: insertError } = await supabase
        .from(tableName)
        .insert([payload]);

      if (insertError) {
        throw insertError;
      }

      setNewTitle('');
      await loadData();
    } catch (err) {
      console.error('[Insert Error]:', err);
      alert(`Insert failed: ${err.message}`);
    } finally {
      setInserting(false);
    }
  }

  return (
    <div
      style={{
        padding: '16px',
        margin: '16px auto',
        maxWidth: '800px',
        borderRadius: '8px',
        backgroundColor: '#1f2937',
        color: '#f9fafb',
        border: '1px solid #374151',
        fontFamily: 'monospace',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, color: '#60a5fa', fontSize: '16px' }}>
          Supabase Diagnostics: <code>{tableName}</code>
        </h3>
        <button
          onClick={loadData}
          disabled={loading}
          style={{
            padding: '4px 10px',
            backgroundColor: '#374151',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div
        style={{
          margin: '12px 0',
          padding: '8px 12px',
          background: '#111827',
          borderRadius: '4px',
          fontSize: '13px',
        }}
      >
        <strong>Active App User: </strong>
        <span style={{ color: '#34d399' }}>{activeEmail}</span>
      </div>

      <form onSubmit={handleAddItem} style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <input
          type="text"
          placeholder="Enter item title..."
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          disabled={inserting}
          style={{
            flex: 1,
            padding: '8px 12px',
            backgroundColor: '#111827',
            border: '1px solid #4b5563',
            color: '#fff',
            borderRadius: '4px',
          }}
        />
        <button
          type="submit"
          disabled={inserting || !newTitle.trim()}
          style={{
            padding: '8px 16px',
            backgroundColor: inserting ? '#4b5563' : '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: inserting ? 'not-allowed' : 'pointer',
          }}
        >
          {inserting ? 'Saving...' : 'Add Item'}
        </button>
      </form>

      {loading && <p style={{ color: '#9ca3af' }}>Loading items...</p>}
      {errorMsg && (
        <div
          style={{
            padding: '10px',
            backgroundColor: '#7f1d1d',
            color: '#fecaca',
            borderRadius: '6px',
            marginBottom: '10px',
          }}
        >
          <strong>Error:</strong> {errorMsg}
        </div>
      )}

      {!loading && !errorMsg && items.length === 0 && (
        <p style={{ color: '#9ca3af' }}>No rows found in {tableName}.</p>
      )}

      {!loading && items.length > 0 && (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {items.map((item) => (
            <li
              key={item.id}
              style={{
                backgroundColor: '#111827',
                padding: '10px 14px',
                borderRadius: '4px',
                marginBottom: '8px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                border: '1px solid #374151',
              }}
            >
              <div>
                <strong>{item.title}</strong>
                {item.user_email && (
                  <span style={{ fontSize: '11px', color: '#9ca3af', marginLeft: '8px' }}>
                    ({item.user_email})
                  </span>
                )}
                {item.created_at && (
                  <span style={{ fontSize: '10px', color: '#6b7280', display: 'block', marginTop: '2px' }}>
                    {new Date(item.created_at).toLocaleTimeString('en-IN', {
                      timeZone: 'Asia/Kolkata',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: true,
                    })}
                  </span>
                )}
              </div>
              <span
                style={{
                  fontSize: '12px',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  backgroundColor: '#1e3a8a',
                  color: '#93c5fd',
                }}
              >
                {item.status || 'pending'}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}