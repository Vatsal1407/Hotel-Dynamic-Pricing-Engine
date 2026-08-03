import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  Tooltip, CartesianGrid, ReferenceDot, Legend,
} from 'recharts';
import type { PriceCurvePoint } from '../api/client';

interface Props {
  curve: PriceCurvePoint[];
  recommendedPrice: number;
}

export default function PriceCurveChart({ curve, recommendedPrice }: Props) {
  const recommended = curve.find(pt => pt.price === recommendedPrice)
    ?? curve.reduce((a, b) => Math.abs(a.price - recommendedPrice) < Math.abs(b.price - recommendedPrice) ? a : b);

  return (
    <div className="rounded-2xl border border-slate-700 bg-gradient-to-br from-slate-800/80 to-slate-900/80 p-6 shadow-xl backdrop-blur">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-4">
        Price vs Expected Revenue Curve
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={curve} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="price"
            tickFormatter={v => `$${v}`}
            stroke="#94a3b8"
            fontSize={11}
            label={{ value: 'Price ($)', position: 'insideBottom', offset: -2, fill: '#94a3b8', fontSize: 11 }}
          />
          <YAxis
            yAxisId="revenue"
            stroke="#94a3b8"
            fontSize={11}
            tickFormatter={v => `$${v}`}
            label={{ value: 'Exp. Revenue', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 11 }}
          />
          <YAxis
            yAxisId="cancel"
            orientation="right"
            stroke="#94a3b8"
            fontSize={11}
            tickFormatter={v => `${(v * 100).toFixed(0)}%`}
            label={{ value: 'Cancel Prob.', angle: 90, position: 'insideRight', fill: '#94a3b8', fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
            labelFormatter={v => `Price: $${v}`}
            formatter={
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              ((value: any, name: any) =>
                name === 'Expected Revenue'
                  ? [`$${Number(value).toFixed(2)}`, name]
                  : [`${(Number(value) * 100).toFixed(1)}%`, name]
              ) as any
            }
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Line
            yAxisId="revenue"
            type="monotone"
            dataKey="expected_revenue"
            name="Expected Revenue"
            stroke="#818cf8"
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 5 }}
          />
          <Line
            yAxisId="cancel"
            type="monotone"
            dataKey="cancellation_probability"
            name="Cancel Probability"
            stroke="#f87171"
            strokeWidth={2}
            strokeDasharray="5 3"
            dot={false}
          />
          {recommended && (
            <ReferenceDot
              yAxisId="revenue"
              x={recommended.price}
              y={recommended.expected_revenue}
              r={7}
              fill="#22c55e"
              stroke="#fff"
              strokeWidth={2}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      <p className="text-center text-xs text-slate-400 mt-2">
        <span className="inline-block w-3 h-3 rounded-full bg-green-500 mr-1 align-middle"></span>
        Recommended price point: <strong className="text-slate-200">${recommendedPrice.toFixed(2)}</strong>
      </p>
    </div>
  );
}
