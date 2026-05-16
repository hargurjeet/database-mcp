'use client';

interface Props {
  filename: string;
  tables: string[];
  onSelect: (table: string) => void;
  loading: boolean;
  onReset: () => void;
}

export default function TableSelector({ filename, tables, onSelect, loading, onReset }: Props) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-xl px-5 py-4">
        <div className="flex items-center gap-3">
          <span className="text-green-400 text-lg">✓</span>
          <div>
            <p className="font-medium text-white">{filename}</p>
            <p className="text-sm text-gray-500">
              {tables.length} table{tables.length !== 1 ? 's' : ''} found
            </p>
          </div>
        </div>
        <button
          onClick={onReset}
          className="text-sm text-gray-600 hover:text-gray-300 transition-colors"
        >
          ← Different file
        </button>
      </div>

      <div>
        <p className="text-xs font-semibold text-gray-600 uppercase tracking-widest mb-3">
          Select a table to inspect
        </p>
        <div className="grid gap-2">
          {tables.map(table => (
            <button
              key={table}
              onClick={() => onSelect(table)}
              disabled={loading}
              className="text-left px-5 py-4 bg-gray-900 hover:bg-gray-800 border border-gray-800 hover:border-blue-600
                         rounded-xl transition-all group disabled:opacity-40 disabled:cursor-wait"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-blue-500 font-mono text-lg">▣</span>
                  <span className="font-mono font-medium text-white">{table}</span>
                </div>
                <span className="text-gray-700 group-hover:text-blue-400 transition-colors text-lg">→</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="text-center py-10 text-gray-500 text-sm">
          <div className="text-3xl mb-3 animate-spin inline-block">⟳</div>
          <p>Running quality checks…</p>
        </div>
      )}
    </div>
  );
}
