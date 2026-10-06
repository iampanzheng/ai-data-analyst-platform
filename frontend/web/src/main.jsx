import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import { formatDisplayValue, formatNumber, friendlyField, friendlyOperation, hasCjk, isPercentageField, niceScale, tokenizeInlineMarkdown } from './presentation.js';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';


function renderInlineMarkdown(text, keyPrefix = 'inline') {
  return tokenizeInlineMarkdown(text).map((part, index) => {
    const key = `${keyPrefix}-${index}`;
    if (part.type === 'strong') return <strong key={key}>{part.text}</strong>;
    if (part.type === 'code') return <code key={key}>{part.text}</code>;
    if (part.type === 'em') return <em key={key}>{part.text}</em>;
    return <React.Fragment key={key}>{part.text}</React.Fragment>;
  });
}

function parseMarkdownRow(line) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => cell.trim());
}

function isMarkdownTableSeparator(line = '') {
  const cells = parseMarkdownRow(line);
  return cells.length > 1 && cells.every(cell => /^:?-{3,}:?$/.test(cell));
}

function SafeMarkdown({ content }) {
  if (!content) return null;
  const lines = String(content).replace(/\r\n/g, '\n').split('\n');
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i += 1; continue; }

    if (line.trim().startsWith('```')) {
      const code = [];
      i += 1;
      while (i < lines.length && !lines[i].trim().startsWith('```')) { code.push(lines[i]); i += 1; }
      if (i < lines.length) i += 1;
      blocks.push(<pre className="markdown-code" key={`code-${i}`}><code>{code.join('\n')}</code></pre>);
      continue;
    }

    if (line.includes('|') && i + 1 < lines.length && isMarkdownTableSeparator(lines[i + 1])) {
      const headers = parseMarkdownRow(line);
      i += 2;
      const rows = [];
      while (i < lines.length && lines[i].trim() && lines[i].includes('|')) {
        rows.push(parseMarkdownRow(lines[i]));
        i += 1;
      }
      blocks.push(
        <div className="markdown-table-wrap" key={`table-${i}`}>
          <table className="markdown-table">
            <thead><tr>{headers.map((cell, index) => <th key={index}>{renderInlineMarkdown(cell, `th-${i}-${index}`)}</th>)}</tr></thead>
            <tbody>{rows.map((row, rowIndex) => <tr key={rowIndex}>{headers.map((_, cellIndex) => <td key={cellIndex}>{renderInlineMarkdown(row[cellIndex] ?? '', `td-${i}-${rowIndex}-${cellIndex}`)}</td>)}</tr>)}</tbody>
          </table>
        </div>
      );
      continue;
    }

    if (/^\s*[-*]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, '').trim());
        i += 1;
      }
      blocks.push(<ul className="markdown-list" key={`list-${i}`}>{items.map((item, index) => <li key={index}>{renderInlineMarkdown(item, `li-${i}-${index}`)}</li>)}</ul>);
      continue;
    }

    const heading = line.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      const level = Math.min(4, heading[1].length + 2);
      const Tag = `h${level}`;
      blocks.push(<Tag className="markdown-heading" key={`heading-${i}`}>{renderInlineMarkdown(heading[2], `heading-${i}`)}</Tag>);
      i += 1;
      continue;
    }

    const paragraph = [line.trim()];
    i += 1;
    while (
      i < lines.length && lines[i].trim() &&
      !lines[i].trim().startsWith('```') &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^(#{1,4})\s+/.test(lines[i]) &&
      !(lines[i].includes('|') && i + 1 < lines.length && isMarkdownTableSeparator(lines[i + 1]))
    ) {
      paragraph.push(lines[i].trim());
      i += 1;
    }
    blocks.push(<p key={`p-${i}`}>{renderInlineMarkdown(paragraph.join(' '), `p-${i}`)}</p>);
  }

  return <div className="safe-markdown">{blocks}</div>;
}

function EvidenceSummary({ report, delivery }) {
  const manifest = delivery?.manifest;
  const findings = report?.key_findings || [];
  const correlation = findings.find(f => f.type === 'correlation');
  const chinese = hasCjk(report?.title || '');

  if (correlation) {
    const r = formatNumber(correlation.pearson_r, 3);
    const x = friendlyField(correlation.x, chinese);
    const y = friendlyField(correlation.y, chinese);
    return (
      <div className="evidence-summary-card">
        <div className="evidence-summary-main">
          <span className="evidence-kicker">{chinese ? '已验证分析结论' : 'Verified analytical result'}</span>
          <strong>{chinese ? `${x} 与 ${y} 的 Pearson r = ${r}` : `${x} ↔ ${y}: Pearson r = ${r}`}</strong>
          <p>{chinese ? `该结果基于 ${correlation.count} 对已验证数值样本。` : `Computed from ${correlation.count} verified numeric observations.`}</p>
        </div>
        <div className="evidence-summary-metrics">
          <span><b>{correlation.count}</b>{chinese ? ' 个样本' : ' observations'}</span>
          {manifest?.row_count != null && <span><b>{manifest.row_count}</b>{chinese ? ' 行查询结果' : ' query rows'}</span>}
          {manifest?.has_chart && <span><b>{delivery?.evidence_snapshot?.chart_artifact?.point_count ?? '—'}</b>{chinese ? ' 个图表点' : ' chart points'}</span>}
        </div>
      </div>
    );
  }

  return (
    <div className="evidence-summary-card">
      <div className="evidence-summary-main">
        <span className="evidence-kicker">{chinese ? '已验证数据摘要' : 'Verified data summary'}</span>
        <strong>{chinese ? `本报告基于 ${manifest?.row_count ?? '—'} 行已验证查询结果。` : `This report is based on ${manifest?.row_count ?? '—'} verified query rows.`}</strong>
        <p>{manifest?.tables?.length ? (chinese ? `涉及数据表：${manifest.tables.join('、')}。` : `Source tables: ${manifest.tables.join(', ')}.`) : report?.summary}</p>
      </div>
    </div>
  );
}

function FindingPresentation({ finding, chinese = false }) {
  if (finding.type === 'correlation') {
    return (
      <article className="verified-finding-card">
        <div className="verified-finding-top">
          <div>
            <span className="finding-label">{chinese ? 'Pearson 相关性' : 'Pearson correlation'}</span>
            <h5>{friendlyField(finding.x, chinese)} <span>↔</span> {friendlyField(finding.y, chinese)}</h5>
          </div>
          <div className="finding-value">r = {formatNumber(finding.pearson_r, 3)}</div>
        </div>
        <div className="finding-support"><span>{finding.count} {chinese ? '个样本' : 'observations'}</span><span className="mono">{finding.evidence_ref}</span></div>
      </article>
    );
  }

  return (
    <article className="verified-finding-card">
      <div className="verified-finding-top"><span className="finding-label">{friendlyField(finding.type)}</span></div>
      <dl>{Object.entries(finding).filter(([key]) => !['type', 'evidence_ref'].includes(key)).map(([key, value]) => { const displayColumn = finding.column || key; return <div key={key}><dt>{friendlyField(key, chinese)}</dt><dd>{typeof value === 'number' ? (key === 'count' ? formatNumber(value, 0) : formatDisplayValue(value, displayColumn, 3)) : friendlyField(String(value), chinese)}</dd></div>; })}</dl>
      {finding.evidence_ref && <div className="finding-support"><span className="mono">{finding.evidence_ref}</span></div>}
    </article>
  );
}

function Pill({ children, tone = 'neutral' }) {
  return <span className={`pill pill-${tone}`}>{children}</span>;
}

function SectionHeader({ eyebrow, title, description, actions }) {
  return (
    <div className="section-header">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="section-actions">{actions}</div>}
    </div>
  );
}

function StatusStrip({ analysis }) {
  if (!analysis) return null;
  return (
    <div className="status-strip">
      <div className="status-item"><span>Route</span><strong>{analysis.selected_route || '—'} → {analysis.final_route || analysis.selected_route || '—'}</strong></div>
      <div className="status-item"><span>Fallback</span><strong>{analysis.fallback_used ? 'Used' : 'No'}</strong></div>
      <div className="status-item"><span>Rows</span><strong>{analysis.query_result?.row_count ?? '—'}</strong></div>
      <div className="status-item"><span>Latency</span><strong>{analysis.query_result?.execution_ms != null ? `${formatNumber(analysis.query_result.execution_ms, 2)} ms` : '—'}</strong></div>
      <div className="status-item"><span>Cost</span><strong>${Number(analysis.estimated_cost_usd || 0).toFixed(6)}</strong></div>
      <div className="status-item"><span>Trace</span><strong className="mono clamp">{analysis.trace_id || '—'}</strong></div>
    </div>
  );
}

function ResultTable({ result }) {
  if (!result?.columns?.length) return <div className="empty-state">No query rows to display.</div>;
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{result.columns.map(c => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {result.rows.map((row, i) => <tr key={i}>{row.map((v, j) => <td key={j}>{formatDisplayValue(v, result.columns[j])}</td>)}</tr>)}
        </tbody>
      </table>
    </div>
  );
}

function AnalysisView({ analysisResult, chinese = false }) {
  if (!analysisResult?.operations?.length) return <div className="empty-state">No controlled Python analysis was requested for this question.</div>;
  return (
    <div className="finding-grid">
      {analysisResult.operations.map((op, index) => (
        <article className="finding-card" key={index}>
          <div className="finding-card-top">
            <Pill tone="verified">Verified</Pill>
            <span className="operation-label">{friendlyOperation(op.operation, chinese)}</span>
          </div>
          <dl>
            {Object.entries(op).filter(([k]) => k !== 'operation').map(([key, value]) => {
              const column = ['min', 'max', 'mean', 'median'].includes(key) ? (op.column || key) : key;
              const display = typeof value === 'number' ? (key === 'pearson_r' ? formatNumber(value, 3) : key === 'count' ? formatNumber(value, 0) : formatDisplayValue(value, column, 3)) : friendlyField(String(value), chinese);
              return <div key={key}><dt>{friendlyField(key, chinese)}</dt><dd>{display}</dd></div>;
            })}
          </dl>
        </article>
      ))}
    </div>
  );
}

function ChartView({ chart }) {
  if (!chart?.points?.length) return <div className="empty-state">No controlled chart artifact was generated.</div>;

  const width = 920;
  const height = 390;
  const pad = { left: 82, right: 28, top: 30, bottom: 78 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const points = chart.points;
  const chinese = hasCjk(chart.title || '');
  const xLabel = friendlyField(chart.x.column, chinese);
  const yLabel = friendlyField(chart.y.column, chinese) + (isPercentageField(chart.y.column) ? ' (%)' : '');

  const yValues = points.map(p => Number(p.y)).filter(Number.isFinite);
  const yMinRaw = Math.min(...yValues);
  const yMaxRaw = Math.max(...yValues);
  const yNice = niceScale(yMinRaw, yMaxRaw, 5, { includeZero: chart.chart_type === 'bar' });
  const yMin = yNice.min;
  const yMax = yNice.max;
  const yScale = y => pad.top + innerH - ((Number(y) - yMin) / (yMax - yMin || 1)) * innerH;
  const yTicks = yNice.ticks;
  const baselineY = yScale(Math.max(yMin, Math.min(yMax, 0)));

  const GridAndYTicks = () => <>
    {yTicks.map((tick, i) => {
      const y = yScale(tick);
      return <g key={`ytick-${i}`}>
        <line x1={pad.left} y1={y} x2={pad.left + innerW} y2={y} className="grid-line" />
        <text x={pad.left - 12} y={y + 4} textAnchor="end" className="tick-label">{formatDisplayValue(tick, chart.y.column, 2)}</text>
      </g>;
    })}
  </>;

  let body;
  if (chart.chart_type === 'scatter') {
    const xValues = points.map(p => Number(p.x)).filter(Number.isFinite);
    const xMinRaw = Math.min(...xValues);
    const xMaxRaw = Math.max(...xValues);
    const xNice = niceScale(xMinRaw, xMaxRaw, 5);
    const xMin = xNice.min;
    const xMax = xNice.max;
    const xScale = x => pad.left + ((Number(x) - xMin) / (xMax - xMin || 1)) * innerW;
    const xTicks = xNice.ticks;
    body = (
      <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={chart.title}>
        <GridAndYTicks />
        {xTicks.map((tick, i) => {
          const x = xScale(tick);
          return <g key={`xtick-${i}`}>
            <line x1={x} y1={pad.top} x2={x} y2={pad.top + innerH} className="grid-line vertical" />
            <text x={x} y={pad.top + innerH + 24} textAnchor="middle" className="tick-label">{formatDisplayValue(tick, chart.x.column, 1)}</text>
          </g>;
        })}
        <line x1={pad.left} y1={pad.top + innerH} x2={pad.left + innerW} y2={pad.top + innerH} className="axis" />
        <line x1={pad.left} y1={pad.top} x2={pad.left} y2={pad.top + innerH} className="axis" />
        {points.map((p, i) => <circle key={i} cx={xScale(p.x)} cy={yScale(p.y)} r="6" className="mark chart-point"><title>{`${xLabel}: ${formatDisplayValue(p.x, chart.x.column)} · ${yLabel}: ${formatDisplayValue(p.y, chart.y.column)}`}</title></circle>)}
        <text x={pad.left + innerW / 2} y={height - 18} textAnchor="middle" className="axis-label">{xLabel}</text>
        <text x="20" y={pad.top + innerH / 2} textAnchor="middle" className="axis-label" transform={`rotate(-90 20 ${pad.top + innerH / 2})`}>{yLabel}</text>
      </svg>
    );
  } else {
    const step = innerW / points.length;
    const centerX = i => pad.left + step * i + step / 2;
    const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${centerX(i)} ${yScale(p.y)}`).join(' ');
    const labelEvery = Math.max(1, Math.ceil(points.length / 10));
    body = (
      <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={chart.title}>
        <GridAndYTicks />
        <line x1={pad.left} y1={baselineY} x2={pad.left + innerW} y2={baselineY} className="axis" />
        <line x1={pad.left} y1={pad.top} x2={pad.left} y2={pad.top + innerH} className="axis" />
        {chart.chart_type === 'bar' && points.map((p, i) => {
          const y = yScale(p.y);
          const top = Math.min(y, baselineY);
          const barH = Math.max(1, Math.abs(baselineY - y));
          return <rect key={i} x={pad.left + step * i + step * 0.16} y={top} width={step * 0.68} height={barH} rx="4" className="mark chart-point"><title>{`${p.x}: ${formatDisplayValue(p.y, chart.y.column)}`}</title></rect>;
        })}
        {chart.chart_type === 'line' && <path d={linePath} fill="none" className="line-mark" />}
        {chart.chart_type === 'line' && points.map((p, i) => <circle key={i} cx={centerX(i)} cy={yScale(p.y)} r="5" className="mark chart-point"><title>{`${p.x}: ${formatDisplayValue(p.y, chart.y.column)}`}</title></circle>)}
        {points.map((p, i) => i % labelEvery === 0 ? <text key={`label-${i}`} x={centerX(i)} y={pad.top + innerH + 24} textAnchor="middle" className="tick-label">{String(p.x)}</text> : null)}
        <text x={pad.left + innerW / 2} y={height - 18} textAnchor="middle" className="axis-label">{xLabel}</text>
        <text x="20" y={pad.top + innerH / 2} textAnchor="middle" className="axis-label" transform={`rotate(-90 20 ${pad.top + innerH / 2})`}>{yLabel}</text>
      </svg>
    );
  }

  return (
    <div className="chart-wrap">
      <div className="chart-title-row">
        <div><h3>{chart.title}</h3><div className="meta">{chart.point_count} points · source: {chart.source}</div></div>
        <Pill tone="verified">Controlled chart</Pill>
      </div>
      {body}
      <div className="chart-hint">Hover a mark to inspect its verified x/y values.</div>
    </div>
  );
}

function downloadBlob(content, type, filename) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function ReportView({ report, delivery }) {
  if (!report) return <div className="empty-state">No controlled report artifact was requested.</div>;
  const chinese = hasCjk(report?.title || '');
  const downloadJson = () => {
    const payload = delivery || report;
    const filename = delivery?.exports?.json_filename || 'analysis-report.json';
    downloadBlob(JSON.stringify(payload, null, 2), 'application/json', filename);
  };
  const downloadMarkdown = () => {
    if (!delivery?.exports?.markdown) return;
    downloadBlob(delivery.exports.markdown, 'text/markdown;charset=utf-8', delivery.exports.markdown_filename || 'analysis-report.md');
  };

  return (
    <div className="report-wrap">
      <div className="report-heading">
        <div>
          <div className="inline-pills"><Pill tone="verified">Verified report</Pill>{report.summary_source && <Pill>Evidence-backed</Pill>}</div>
          <h3>{report.title}</h3>
          <div className="meta">source: {report.source}</div>
        </div>
        <div className="export-actions">
          <button className="secondary" onClick={downloadJson}>{delivery ? 'Download JSON' : 'Export JSON'}</button>
          {delivery?.exports?.markdown && <button className="secondary" onClick={downloadMarkdown}>Download Markdown</button>}
        </div>
      </div>
      {report.summary && <div className="report-section"><h4>Evidence summary</h4><EvidenceSummary report={report} delivery={delivery} /></div>}
      <details className="technical-evidence"><summary>Technical evidence</summary><div className="technical-evidence-body"><p>{report.summary}</p><div className="technical-chip-row"><Pill>{delivery?.manifest?.row_count ?? '—'} rows</Pill>{delivery?.manifest?.tables?.map(table => <Pill key={table}>{table}</Pill>)}{delivery?.manifest?.has_analysis && <Pill>Controlled analysis</Pill>}{delivery?.manifest?.has_chart && <Pill>Controlled chart</Pill>}</div></div></details>
      {report.key_findings?.length > 0 && (
        <div className="report-section"><h4>Verified findings</h4><div className="verified-findings-grid">
          {report.key_findings.map((finding, i) => <FindingPresentation finding={finding} chinese={chinese} key={i} />)}
        </div></div>
      )}
    </div>
  );
}

function ProvenanceView({ analysis }) {
  const [copied, setCopied] = useState(false);
  if (!analysis) return <div className="empty-state">Run an analysis to inspect provenance.</div>;
  const delivery = analysis.delivery_artifact;
  const manifest = delivery?.manifest;
  const copyTrace = async () => {
    if (!analysis.trace_id || !navigator?.clipboard) return;
    await navigator.clipboard.writeText(analysis.trace_id);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  };
  return (
    <div className="provenance-grid">
      <article className="provenance-card trace-card"><span>Trace ID</span><div className="provenance-value-row"><strong className="mono break-all">{analysis.trace_id || '—'}</strong>{analysis.trace_id && <button className="copy-button" onClick={copyTrace}>{copied ? 'Copied' : 'Copy'}</button>}</div></article>
      <article className="provenance-card"><span>Model</span><strong>{analysis.model || '—'}</strong></article>
      <article className="provenance-card"><span>Provider</span><strong>{analysis.provider || '—'}</strong></article>
      <article className="provenance-card"><span>Tokens</span><strong>{analysis.usage?.total_tokens ?? '—'}</strong></article>
      <article className="provenance-card"><span>Delivery format</span><strong>{delivery?.format_version || '—'}</strong></article>
      <article className="provenance-card"><span>Verified source</span><strong>{(delivery?.source || analysis.report_artifact?.source) === 'verified_artifacts' ? 'Verified artifacts' : (delivery?.source || analysis.report_artifact?.source || '—')}</strong></article>
      {manifest && <article className="provenance-card wide"><span>Artifact manifest</span><div className="manifest-badges"><Pill>{manifest.row_count} rows</Pill>{manifest.tables?.map(t => <Pill key={t}>{t}</Pill>)}<Pill tone={manifest.has_analysis ? 'verified' : 'neutral'}>Analysis {manifest.has_analysis ? 'yes' : 'no'}</Pill><Pill tone={manifest.has_chart ? 'verified' : 'neutral'}>Chart {manifest.has_chart ? 'yes' : 'no'}</Pill><Pill tone={manifest.has_report ? 'verified' : 'neutral'}>Report {manifest.has_report ? 'yes' : 'no'}</Pill></div></article>}
    </div>
  );
}

function WorkspaceTabs({ analysis, result, sql }) {
  const [tab, setTab] = useState('data');
  const tabs = [
    ['data', 'Data'], ['analysis', 'Analysis'], ['chart', 'Chart'], ['report', 'Report'], ['provenance', 'Provenance']
  ];
  return (
    <section className="workspace-panel">
      <div className="tabs" role="tablist" aria-label="Analysis workspace sections">
        {tabs.map(([id, label]) => <button key={id} className={`tab ${tab === id ? 'active' : ''}`} onClick={() => setTab(id)}>{label}</button>)}
      </div>
      <div className="tab-panel">
        {tab === 'data' && <>
          <SectionHeader eyebrow="Verified query" title="Data result" description="Read-only PostgreSQL output after SQL validation." />
          <ResultTable result={result} />
          <details className="tech-details"><summary>Validated SQL</summary><pre>{sql || '—'}</pre></details>
        </>}
        {tab === 'analysis' && <><SectionHeader eyebrow="Controlled Python" title="Analysis" description="Deterministic operations over verified query rows." /><AnalysisView analysisResult={analysis?.analysis_result} chinese={hasCjk(analysis?.question || '')} /></>}
        {tab === 'chart' && <><SectionHeader eyebrow="Controlled visualization" title="Chart" description="Structured chart artifact generated only from verified query columns." /><ChartView chart={analysis?.chart_artifact} /></>}
        {tab === 'report' && <><SectionHeader eyebrow="Evidence-bound reporting" title="Report & delivery" description="Verified report summary plus deterministic JSON/Markdown delivery exports." /><ReportView report={analysis?.report_artifact} delivery={analysis?.delivery_artifact} /></>}
        {tab === 'provenance' && <><SectionHeader eyebrow="Trust boundary" title="Provenance" description="Trace, model, routing, and delivery metadata for the current analysis." /><ProvenanceView analysis={analysis} /></>}
      </div>
    </section>
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
  const hasWorkspace = Boolean(analysis || result);

  useEffect(() => {
    fetch(`${API}/schema`).then(async r => {
      if (!r.ok) throw new Error(`Schema request failed: ${r.status}`);
      return r.json();
    }).then(setSchema).catch(e => setError(e.message));
  }, []);

  const capabilityPills = useMemo(() => ['Validated SQL', 'Controlled Python', 'Charts', 'Reports', 'Delivery provenance'], []);

  async function askAnalyst() {
    setLoading(true); setError(null);
    try {
      const r = await fetch(`${API}/analyze`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, routingMode, fallbackMode })
      });
      const body = await r.json();
      if (!r.ok) throw new Error(body?.detail?.message || JSON.stringify(body));
      setAnalysis(body); setResult(body.query_result);
      if (body.validated_sql) setSql(body.validated_sql);
      if (body.errors?.length) throw new Error(body.errors.map(e => `${e.code}: ${e.message}`).join('\n'));
    } catch (e) {
      setAnalysis(null); setResult(null); setError(e.message);
    } finally { setLoading(false); }
  }

  async function runQuery() {
    setLoading(true); setError(null);
    try {
      const r = await fetch(`${API}/query`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sql }) });
      const body = await r.json();
      if (!r.ok) throw new Error(body?.detail?.message || JSON.stringify(body));
      setResult(body);
    } catch (e) { setResult(null); setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <div className="eyebrow">P1 · AI Engineer Portfolio</div>
          <h1>AI Data Analyst</h1>
          <p>Ask a business question, inspect the verified data path, and export evidence-bound analytical deliverables.</p>
          <div className="capability-row">{capabilityPills.map(x => <Pill key={x}>{x}</Pill>)}</div>
        </div>
        <div className="trust-card">
          <span>Trust model</span>
          <strong>LLM proposes. Deterministic controls verify.</strong>
          <small>SQL validation · read-only execution · controlled analysis · verified artifacts</small>
        </div>
      </header>

      <div className="workspace-grid">
        <aside className="control-panel">
          <SectionHeader eyebrow="Ask the analyst" title="Analysis request" description="Natural-language question with explicit routing and fallback policy." />
          <label htmlFor="question">Business question</label>
          <textarea id="question" value={question} onChange={e => setQuestion(e.target.value)} rows={6} />
          <div className="field-grid">
            <div><label htmlFor="routing-mode">LLM route</label><select id="routing-mode" value={routingMode} onChange={e => setRoutingMode(e.target.value)}><option value="auto">Auto</option><option value="remote">Remote</option><option value="local">Local</option></select></div>
            <div><label htmlFor="fallback-mode">Fallback</label><select id="fallback-mode" value={fallbackMode} onChange={e => setFallbackMode(e.target.value)}><option value="auto">Auto</option><option value="disabled">Disabled</option><option value="cross_route">Cross-route</option></select></div>
          </div>
          <button className="primary full" onClick={askAnalyst} disabled={loading || !question.trim()}>{loading ? 'Analyzing…' : 'Run analysis'}</button>

          <details className="manual-query">
            <summary>Manual validated SQL</summary>
            <textarea value={sql} onChange={e => setSql(e.target.value)} rows={7} />
            <button className="secondary full" onClick={runQuery} disabled={loading || !sql.trim()}>Run query only</button>
          </details>

          {schema && <details className="schema-browser"><summary>Available schema · {schema.tables?.length || 0} tables</summary>{schema.tables.map(t => <details key={t.table_name} className="schema-table"><summary>{t.table_name}</summary><div className="schema-columns">{t.columns.map(c => <div key={c.name}><strong>{c.name}</strong><span>{c.data_type} · {c.semantic_type}</span></div>)}</div></details>)}</details>}
        </aside>

        <section className="results-column">
          {error && <div className="error-banner"><strong>Analysis error</strong><span>{error}</span></div>}
          {analysis?.final_answer && (
            <section className="answer-card">
              <div className="answer-top"><div><div className="eyebrow">LLM answer</div><h2>Answer</h2></div><div className="inline-pills"><Pill>LLM-generated</Pill><Pill tone={analysis.fallback_used ? 'warn' : 'verified'}>{analysis.fallback_used ? 'Fallback used' : 'Primary route'}</Pill></div></div>
              <div className="answer-copy"><SafeMarkdown content={analysis.final_answer} /></div>
              <StatusStrip analysis={analysis} />
            </section>
          )}
          {hasWorkspace ? <WorkspaceTabs analysis={analysis} result={result} sql={sql} /> : (
            <section className="empty-workspace"><div className="empty-icon">↗</div><h2>Your analysis workspace is ready</h2><p>Run a question to populate verified data, controlled analysis, charts, reports, and provenance.</p></section>
          )}
        </section>
      </div>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
