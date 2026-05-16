'use client';

import { useCallback, useState } from 'react';

interface Props {
  onUpload: (file: File) => void;
  loading: boolean;
}

export default function FileUpload({ onUpload, loading }: Props) {
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  const pick = useCallback((f: File) => {
    if (!f.name.endsWith('.db')) {
      alert('Please select a .db (DuckDB) file');
      return;
    }
    setFile(f);
  }, []);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files[0]) pick(e.dataTransfer.files[0]);
  };

  return (
    <div className="space-y-5">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => document.getElementById('db-file-input')?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-20 text-center cursor-pointer transition-all select-none
          ${dragging
            ? 'border-blue-500 bg-blue-950/20'
            : file
              ? 'border-green-700 bg-green-950/10'
              : 'border-gray-700 bg-gray-900/50 hover:border-gray-500 hover:bg-gray-900'
          }`}
      >
        <div className="text-5xl mb-4">{file ? '✅' : '🗄️'}</div>
        <p className="text-lg font-semibold text-white">
          {file ? file.name : 'Drop your .db file here'}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          {file
            ? `${(file.size / 1024).toFixed(1)} KB — ready`
            : 'or click to browse  ·  DuckDB files only (.db)'}
        </p>
        <input
          id="db-file-input"
          type="file"
          accept=".db"
          className="hidden"
          onChange={e => { if (e.target.files?.[0]) pick(e.target.files[0]); }}
        />
      </div>

      {file && (
        <button
          onClick={() => onUpload(file)}
          disabled={loading}
          className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-blue-900/50 disabled:cursor-wait text-white font-semibold transition-colors"
        >
          {loading ? 'Uploading & discovering tables…' : 'Analyse Database →'}
        </button>
      )}
    </div>
  );
}
