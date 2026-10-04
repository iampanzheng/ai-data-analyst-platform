import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';


function ChartView({ chart }) {
  if (!chart?.points?.length) return null;

  const width = 920;
  const height = 360;
  const pad = { left: 64, right: 24, top: 28, bottom: 72 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const points = chart.points;
  const yValues = points.map(p => Number(p.y));
  const minY = Math.min(...yValues, 0);
  const maxYRaw = Math.max(...yValues, 0);
  const maxY = maxYRaw === minY ? minY + 1 : maxYRaw;
  const yScale = y => pad.top + innerH - ((Number(y) - minY) / (maxY - minY)) * innerH;
  const baselineY = yScale(0);

  if (chart.chart_type === 'scatter') {
    const xValues = points.map(p => Number(p.x));
    const minX = Math.min(...xValues);
    const maxXRaw = Math.max(...xValues);
    const maxX = maxXRaw === minX ? minX + 1 : maxXRaw;
    const xScale = x => pad.left + ((Number(x) - minX) / (maxX - minX)) * innerW;
    return (
      <div className="chart-wrap">
        <h2>{chart.title}</h2>
        <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={chart.title}>
          <line x1={pad.left} y1={pad.top + innerH} x2={pad.left + innerW} y2={pad.top + innerH} className="axis" />
          <line x1={pad.left} y1={pad.top} x2={pad.left} y2={pad.top + innerH} className="axis" />
          {points.map((p, i) => (
            <circle key={i} cx={xScale(p.x)} cy={yScale(p.y)} r="5" className="mark" />
          ))}
          <text x={pad.left + innerW / 2} y={height - 18} textAnchor="middle" className="axis-label">{chart.x.column}</text>
          <text x="18" y={pad.top + innerH / 2} textAnchor="middle" className="axis-label" transform={`rotate(-90 18 ${pad.top + innerH / 2})`}>{chart.y.column}</text>
        </svg>
        <div className="meta">{chart.point_count} points · source: {chart.source}</div>
      </div>
    );
  }

  const step = innerW / points.length;
  const centerX = i => pad.left + step * i + step / 2;
  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${centerX(i)} ${yScale(p.y)}`).join(' ');
  const labelEvery = Math.max(1, Math.ceil(points.length / 10));

  return (
    <div className="chart-wrap">
      <h2>{chart.title}</h2>
      <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={chart.title}>
        <line x1={pad.left} y1={baselineY} x2={pad.left + innerW} y2={baselineY} className="axis" />
        <line x1={pad.left} y1={pad.top} x2={pad.left} y2={pad.top + innerH} className="axis" />
        {chart.chart_type === 'bar' && points.map((p, i) => {
          const y = yScale(p.y);
          const top = Math.min(y, baselineY);
          const barH = Math.max(1, Math.abs(baselineY - y));
          return <rect key={i} x={pad.left + step * i + step * 0.16} y={top} width={step * 0.68} height={barH} rx="3" className="mark" />;
        })}
        {chart.chart_type === 'line' && <path d={linePath} fill="none" className="line-mark" />}
        {chart.chart_type === 'line' && points.map((p, i) => <circle key={i} cx={centerX(i)} cy={yScale(p.y)} r="4" className="mark" />)}
        {points.map((p, i) => i % labelEvery === 0 ? (
          <text key={`label-${i}`} x={centerX(i)} y={height - 34} textAnchor="middle" className="tick-label">{String(p.x)}</text>
        ) : null)}
        <text x={pad.left + innerW / 2} y={height - 10} textAnchor="middle" className="axis-label">{chart.x.column}</text>
        <text x="18" y={pad.top + innerH / 2} textAnchor="middle" className="axis-label" transform={`rotate(-90 18 ${pad.top + innerH / 2})`}>{chart.y.column}</text>
      </svg>
      <div className="meta">{chart.point_count} points · source: {chart.source}</div>
    </div>
  );
}

function App() {
  const [question, setQuestion] = useState('人口最多的 5 个城市是哪几个？');
  const [analysis, setAnalysis] = useState(null);
  const [routingMode, setRoutingMode] = useState('auto');
  const [fallbackMode, setFallbackMode] = useState('auto');
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

  async function askAnalyst() {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${API}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, routingMode, fallbackMode })
      });
      const body = await r.json();
      if (!r.ok) throw new Error(body?.detail?.message || JSON.stringify(body));
      setAnalysis(body);
      setResult(body.query_result);
      if (body.validated_sql) setSql(body.validated_sql);
      if (body.errors?.length) throw new Error(body.errors.map(e => `${e.code}: ${e.message}`).join('\n'));
    } catch (e) {
      setAnalysis(null);
      setResult(null);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

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
        <p>Question → validated SQL → controlled analysis → controlled visualization → evidence-backed answer</p>
      </header>

      <section className="card">
        <label htmlFor="question">Business Question</label>
        <textarea id="question" value={question} onChange={e => setQuestion(e.target.value)} rows={4} />
        <label htmlFor="routing-mode">LLM Route</label>
        <select id="routing-mode" value={routingMode} onChange={e => setRoutingMode(e.target.value)}>
          <option value="auto">Auto (measured default)</option>
          <option value="remote">Remote / interactive</option>
          <option value="local">Local / privacy</option>
        </select>
        <label htmlFor="fallback-mode">Fallback</label>
        <select id="fallback-mode" value={fallbackMode} onChange={e => setFallbackMode(e.target.value)}>
          <option value="auto">Auto / privacy-safe</option>
          <option value="disabled">Disabled</option>
          <option value="cross_route">Allow cross-route</option>
        </select>
        <button onClick={askAnalyst} disabled={loading || !question.trim()}>
          {loading ? 'Analyzing…' : 'Ask Analyst'}
        </button>
      </section>

      {analysis?.final_answer && (
        <section className="card">
          <h2>Answer</h2>
          <p>{analysis.final_answer}</p>
          <div className="meta">Model: {analysis.model || '—'} · route: {analysis.selected_route || '—'}→{analysis.final_route || analysis.selected_route || '—'} · fallback: {analysis.fallback_used ? 'used' : 'no'} · cost: ${Number(analysis.estimated_cost_usd || 0).toFixed(6)} · trace: {analysis.trace_id}</div>
        </section>
      )}

      {analysis?.chart_artifact && (
        <section className="card">
          <ChartView chart={analysis.chart_artifact} />
        </section>
      )}

      {error && <section className="card error"><strong>Error:</strong> {error}</section>}

      <section className="card">
        <label htmlFor="sql">Validated SQL / Manual Query</label>
        <textarea id="sql" value={sql} onChange={e => setSql(e.target.value)} rows={7} />
        <button onClick={runQuery} disabled={loading || !sql.trim()}>Run Query</button>
      </section>

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
