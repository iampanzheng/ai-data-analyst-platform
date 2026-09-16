import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';

function App() {
  const [sql, setSql] = useState('SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5');
  const [result, setResult] = useState(null);
  const [schema, setSchema] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/schema`).then(async r => {
      if (!r.ok) throw new Error(`Schema request failed: ${r.status}`);
      return r.json();
    }).then(setSchema).catch(e => setError(e.message));
  }, []);

  async function runQuery() {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${API}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql })
      });
      const body = await r.json();
      if (!r.ok) throw new Error(body?.detail?.message || JSON.stringify(body));
      setResult(body);
    } catch (e) {
      setResult(null);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <header>
        <h1>AI Data Analyst</h1>
        <p>Day 4 scaffold: React → Spring Boot → FastAPI → PostgreSQL</p>
      </header>

      <section className="card">
        <label htmlFor="sql">SQL Query</label>
        <textarea id="sql" value={sql} onChange={e => setSql(e.target.value)} rows={7} />
        <button onClick={runQuery} disabled={loading || !sql.trim()}>
          {loading ? 'Running…' : 'Run Query'}
        </button>
      </section>

      {error && <section className="card error"><strong>Error:</strong> {error}</section>}

      {result && (
        <section className="card">
          <h2>Result</h2>
          <div className="meta">Rows: {result.row_count} · {result.execution_ms} ms · trace: {result.trace_id}</div>
          <div className="table-wrap">
            <table>
              <thead><tr>{result.columns.map(c => <th key={c}>{c}</th>)}</tr></thead>
              <tbody>
                {result.rows.map((row, i) => <tr key={i}>{row.map((v, j) => <td key={j}>{String(v ?? '')}</td>)}</tr>)}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {schema && (
        <section className="card">
          <h2>Available Schema</h2>
          {schema.tables.map(t => (
            <details key={t.table_name}>
              <summary>{t.table_name} — {t.description}</summary>
              <table>
                <thead><tr><th>Column</th><th>Type</th><th>Semantic</th><th>Description</th></tr></thead>
                <tbody>{t.columns.map(c => <tr key={c.name}><td>{c.name}</td><td>{c.data_type}</td><td>{c.semantic_type}</td><td>{c.description || '—'}</td></tr>)}</tbody>
              </table>
            </details>
          ))}
        </section>
      )}
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
