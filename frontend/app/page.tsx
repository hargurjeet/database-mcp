'use client';

import { useState } from 'react';
import FileUpload from '@/components/FileUpload';
import TableSelector from '@/components/TableSelector';
import ResultsDashboard, { CheckResults } from '@/components/ResultsDashboard';

type Step = 'upload' | 'select' | 'results';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [step, setStep] = useState<Step>('upload');
  const [dbPath, setDbPath] = useState('');
  const [filename, setFilename] = useState('');
  const [tables, setTables] = useState<string[]>([]);
  const [selectedTable, setSelectedTable] = useState('');
  const [results, setResults] = useState<CheckResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleUpload(file: File) {
    setLoading(true);
    setError('');
    try {
      const form = new FormData();
      form.append('file', file);
      const up = await fetch(`${API}/upload`, { method: 'POST', body: form });
      if (!up.ok) throw new Error((await up.json()).detail ?? 'Upload failed');
      const { db_path, filename: name } = await up.json();

      const tbl = await fetch(`${API}/tables?db_path=${encodeURIComponent(db_path)}`);
      if (!tbl.ok) throw new Error('Could not list tables');
      const { tables: t } = await tbl.json();

      setDbPath(db_path);
      setFilename(name);
      setTables(t);
      setStep('select');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectTable(table: string) {
    setSelectedTable(table);
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/check/${table}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ db_type: 'duckdb', db_path: dbPath }),
      });
      if (!res.ok) throw new Error((await res.json()).detail ?? 'Check failed');
      setResults(await res.json());
      setStep('results');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setStep('upload');
    setDbPath('');
    setFilename('');
    setTables([]);
    setSelectedTable('');
    setResults(null);
    setError('');
  }

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <header className="mb-10">
          <h1 className="text-3xl font-bold text-white tracking-tight">DB Quality Inspector</h1>
          <p className="text-gray-500 mt-1 text-sm">
            Upload a DuckDB file — auto-detect tables, run quality checks, view results instantly.
          </p>
        </header>

        <StepIndicator current={step} />

        {error && (
          <div className="mt-6 bg-red-950/50 border border-red-800 text-red-300 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="mt-8">
          {step === 'upload' && (
            <FileUpload onUpload={handleUpload} loading={loading} />
          )}
          {step === 'select' && (
            <TableSelector
              filename={filename}
              tables={tables}
              onSelect={handleSelectTable}
              loading={loading}
              onReset={reset}
            />
          )}
          {step === 'results' && results && (
            <ResultsDashboard
              table={selectedTable}
              filename={filename}
              results={results}
              onReset={reset}
            />
          )}
        </div>
      </div>
    </main>
  );
}

function StepIndicator({ current }: { current: Step }) {
  const steps: { key: Step; label: string }[] = [
    { key: 'upload', label: 'Upload' },
    { key: 'select', label: 'Select Table' },
    { key: 'results', label: 'Results' },
  ];
  const idx = steps.findIndex(s => s.key === current);

  return (
    <div className="flex items-center gap-2">
      {steps.map((s, i) => (
        <div key={s.key} className="flex items-center gap-2">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors
            ${i < idx  ? 'bg-green-900/40 text-green-400' :
              i === idx ? 'bg-blue-600 text-white' :
                          'bg-gray-800 text-gray-600'}`}>
            <span>{i + 1}</span>
            <span>{s.label}</span>
          </div>
          {i < steps.length - 1 && (
            <div className={`h-px w-6 ${i < idx ? 'bg-green-800' : 'bg-gray-800'}`} />
          )}
        </div>
      ))}
    </div>
  );
}
