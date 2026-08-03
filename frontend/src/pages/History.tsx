import { useEffect, useState } from 'react';
import { getHistory, type HistoryItem } from '../api/client';

export default function History() {
  const [rows, setRows] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHistory(100)
      .then(setRows)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
          Request History
        </h1>
        <p className="text-slate-400 mt-1 text-sm">
          Recent pricing recommendations logged by the system.
        </p>
      </div>

      {loading && (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
        </div>
      )}

      {error && (
        <div className="rounded-xl bg-rose-950/40 border border-rose-800 p-4 text-sm text-rose-300">
          ⚠️ {error}
        </div>
      )}

      {!loading && !error && rows.length === 0 && (
        <div className="text-center py-16 text-slate-500">
          <p className="text-4xl mb-3">📭</p>
          <p>No recommendations yet. Use the Recommender to get started.</p>
        </div>
      )}

      {!loading && rows.length > 0 && (
        <div className="overflow-x-auto rounded-2xl border border-slate-700 shadow-xl">
          <table className="w-full text-sm">
            <thead className="bg-slate-800/80 text-slate-300 text-xs uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3 text-left">#</th>
                <th className="px-4 py-3 text-left">Date</th>
                <th className="px-4 py-3 text-left">Segment</th>
                <th className="px-4 py-3 text-left">Country</th>
                <th className="px-4 py-3 text-right">Occupancy</th>
                <th className="px-4 py-3 text-right">Rec. Price</th>
                <th className="px-4 py-3 text-right">Exp. Revenue</th>
                <th className="px-4 py-3 text-right">Cancel Prob.</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {rows.map(r => (
                <tr key={r.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-3 text-slate-400 font-mono">{r.id}</td>
                  <td className="px-4 py-3 text-slate-300">
                    {r.created_at ? new Date(r.created_at).toLocaleString() : '—'}
                  </td>
                  <td className="px-4 py-3 text-slate-300">{String(r.input_payload?.market_segment ?? '—')}</td>
                  <td className="px-4 py-3 text-slate-300">{String(r.input_payload?.country ?? '—')}</td>
                  <td className="px-4 py-3 text-right text-slate-300">
                    {r.occupancy_rate != null ? `${(r.occupancy_rate * 100).toFixed(0)}%` : '—'}
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-indigo-300">
                    {r.recommended_price != null ? `$${r.recommended_price.toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-3 text-right text-amber-300">
                    {r.expected_revenue != null ? `$${r.expected_revenue.toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {r.cancellation_probability != null ? (
                      <span className={
                        r.cancellation_probability < 0.3 ? 'text-emerald-400' :
                        r.cancellation_probability <= 0.6 ? 'text-amber-400' : 'text-rose-400'
                      }>
                        {(r.cancellation_probability * 100).toFixed(1)}%
                      </span>
                    ) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
