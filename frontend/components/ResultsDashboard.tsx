'use client';

import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';

export interface CheckResults {
  schema: Array<{ column: string; type: string }>;
  null_rates: Record<string, number>;
  row_count: { table: string; total_rows: number };
  distribution_stats: Record<string, {
    column: string;
    mean: number | null;
    std: number | null;
    min: number | null;
    max: number | null;
    count: number;
    z_score_threshold: number;
  }>;
  cardinality: Record<string, {
    column: string;
    distinct_count: number;
    top_values: Array<{ value: string | null; freq: number }>;
  }>;
  timestamp_gaps: Record<string, {
    column: string;
    row_count: number;
    min_ts?: string;
    max_ts?: string;
    median_gap_seconds?: number;
    max_gap_seconds?: number;
    large_gaps_detected: boolean;
    large_gap_count?: number;
    detail?: string;
  }>;
}

interface Props {
  table: string;
  filename: string;
  results: CheckResults;
  onReset: () => void;
}

function f(n: number | null | undefined, dp = 2) {
  return n == null ? 'N/A' : n.toFixed(dp);
}

function secs(s: number) {
  if (s < 60) return `${s.toFixed(0)}s`;
  if (s < 3600) return `${(s / 60).toFixed(1)}m`;
  if (s < 86400) return `${(s / 3600).toFixed(1)}h`;
  return `${(s / 86400).toFixed(1)}d`;
}

export default function ResultsDashboard({ table, filename, results, onReset }: Props) {
  const nullyCols = Object.values(results.null_rates).filter(r => r > 0).length;
  const hasDistrib = Object.keys(results.distribution_stats).length > 0;
  const hasCard    = Object.keys(results.cardinality).length > 0;
  const hasTs      = Object.keys(results.timestamp_gaps).length > 0;

  const nullData = Object.entries(results.null_rates).map(([col, rate]) => ({
    col,
    pct: Math.round(rate * 100),
  }));

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white font-mono">{table}</h2>
          <p className="text-gray-600 text-sm mt-0.5">{filename}</p>
        </div>
        <button onClick={onReset} className="text-sm text-gray-600 hover:text-gray-300 transition-colors mt-1">
          ← Start over
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card label="Total Rows" value={results.row_count.total_rows.toLocaleString()} />
        <Card label="Columns" value={results.schema.length} />
        <Card label="Columns with Nulls" value={nullyCols} warn={nullyCols > 0} />
      </div>

      {/* Schema + null rates side-by-side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Section title="Schema">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-600 border-b border-gray-800">
                <th className="pb-2 font-medium pr-6">Column</th>
                <th className="pb-2 font-medium pr-6">Type</th>
                <th className="pb-2 font-medium">Null %</th>
              </tr>
            </thead>
            <tbody>
              {results.schema.map(col => {
                const rate = results.null_rates[col.column] ?? 0;
                return (
                  <tr key={col.column} className="border-b border-gray-800/40">
                    <td className="py-2 pr-6 font-mono text-blue-300 text-xs">{col.column}</td>
                    <td className="py-2 pr-6 text-gray-500 text-xs">{col.type}</td>
                    <td className={`py-2 text-xs font-medium ${rate > 0 ? 'text-amber-400' : 'text-green-400'}`}>
                      {(rate * 100).toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Section>

        <Section title="Null Rates">
          <ResponsiveContainer width="100%" height={Math.max(100, nullData.length * 42)}>
            <BarChart data={nullData} layout="vertical" margin={{ left: 8, right: 32, top: 4, bottom: 4 }}>
              <XAxis
                type="number"
                domain={[0, 100]}
                tickFormatter={v => `${v}%`}
                tick={{ fill: '#4b5563', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="col"
                tick={{ fill: '#93c5fd', fontSize: 12, fontFamily: 'monospace' }}
                width={110}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                formatter={(v: number) => [`${v}%`, 'Null rate']}
                contentStyle={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, fontSize: 12 }}
              />
              <Bar dataKey="pct" radius={[0, 4, 4, 0]}>
                {nullData.map(entry => (
                  <Cell key={entry.col} fill={entry.pct > 0 ? '#f59e0b' : '#10b981'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>
      </div>

      {/* Distribution stats */}
      {hasDistrib && (
        <Section title="Distribution Stats — Numeric Columns">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.values(results.distribution_stats).map(stat => (
              <div key={stat.column} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <p className="font-mono text-blue-300 font-semibold mb-3 text-sm">{stat.column}</p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
                  <KV k="Mean"      v={f(stat.mean)} />
                  <KV k="Std Dev"   v={f(stat.std)} />
                  <KV k="Min"       v={f(stat.min)} />
                  <KV k="Max"       v={f(stat.max)} />
                  <KV k="Count"     v={stat.count} />
                  <KV k="Z-thresh"  v={stat.z_score_threshold} />
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Cardinality */}
      {hasCard && (
        <Section title="Cardinality — String Columns">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.values(results.cardinality).map(card => (
              <div key={card.column} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <p className="font-mono text-blue-300 font-semibold text-sm">{card.column}</p>
                  <span className="text-xs text-gray-600 bg-gray-800 px-2 py-0.5 rounded-full">
                    {card.distinct_count} distinct
                  </span>
                </div>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-gray-600 text-left">
                      <th className="font-normal pb-1.5">Value</th>
                      <th className="font-normal pb-1.5 text-right">Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {card.top_values.slice(0, 5).map((v, i) => (
                      <tr key={i} className="border-t border-gray-800/50">
                        <td className="py-1 font-mono text-gray-300">
                          {v.value == null
                            ? <span className="italic text-gray-600">null</span>
                            : String(v.value)}
                        </td>
                        <td className="py-1 text-right text-gray-500">{v.freq}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Timestamp gaps */}
      {hasTs && (
        <Section title="Timestamp Gaps">
          <div className="grid gap-3">
            {Object.values(results.timestamp_gaps).map(gap => (
              <div
                key={gap.column}
                className={`rounded-xl p-4 border ${
                  gap.large_gaps_detected
                    ? 'border-amber-800/60 bg-amber-950/20'
                    : 'border-gray-800 bg-gray-900'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-base">{gap.large_gaps_detected ? '⚠️' : '✅'}</span>
                  <p className="font-mono text-blue-300 font-semibold text-sm">{gap.column}</p>
                  {gap.large_gaps_detected && (
                    <span className="text-xs bg-amber-900/50 text-amber-400 px-2 py-0.5 rounded-full">
                      {gap.large_gap_count} large gap{gap.large_gap_count !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
                {gap.min_ts ? (
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
                    <KV k="From"        v={gap.min_ts.replace('T', ' ').slice(0, 19)} />
                    <KV k="To"          v={(gap.max_ts ?? '').replace('T', ' ').slice(0, 19)} />
                    <KV k="Median gap"  v={secs(gap.median_gap_seconds ?? 0)} />
                    <KV k="Max gap"     v={secs(gap.max_gap_seconds ?? 0)} />
                  </div>
                ) : (
                  <p className="text-xs text-gray-600">{gap.detail}</p>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-xs font-bold text-gray-600 uppercase tracking-widest mb-4">{title}</h3>
      {children}
    </div>
  );
}

function Card({ label, value, warn }: { label: string; value: React.ReactNode; warn?: boolean }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-gray-600 text-xs font-medium uppercase tracking-wide">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${warn ? 'text-amber-400' : 'text-white'}`}>{value}</p>
    </div>
  );
}

function KV({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <>
      <span className="text-gray-600">{k}</span>
      <span className="text-gray-200 text-right tabular-nums">{v}</span>
    </>
  );
}
