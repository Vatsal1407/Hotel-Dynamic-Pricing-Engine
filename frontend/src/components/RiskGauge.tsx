interface Props {
  probability: number;
}

export default function RiskGauge({ probability }: Props) {
  const pct = Math.round(probability * 100);
  const category = probability < 0.3 ? 'Low' : probability <= 0.6 ? 'Medium' : 'High';

  const color = probability < 0.3
    ? 'from-emerald-500 to-emerald-400'
    : probability <= 0.6
      ? 'from-amber-500 to-yellow-400'
      : 'from-rose-600 to-red-400';

  const ringColor = probability < 0.3
    ? 'text-emerald-400'
    : probability <= 0.6
      ? 'text-amber-400'
      : 'text-rose-500';

  const bgRing = 'text-slate-700';

  // SVG arc for the gauge
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (probability * circumference);

  return (
    <div className="rounded-2xl border border-slate-700 bg-gradient-to-br from-slate-800/80 to-slate-900/80 p-6 shadow-xl backdrop-blur flex flex-col items-center">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-4">
        Cancellation Risk
      </h3>

      <div className="relative w-32 h-32 mb-3">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r={radius} fill="none" strokeWidth="10"
            className={`stroke-current ${bgRing}`} />
          <circle cx="60" cy="60" r={radius} fill="none" strokeWidth="10"
            strokeLinecap="round"
            className={`stroke-current ${ringColor} transition-all duration-700`}
            strokeDasharray={circumference}
            strokeDashoffset={offset} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-white">{pct}%</span>
        </div>
      </div>

      <span className={`inline-block rounded-full bg-gradient-to-r ${color} px-4 py-1 text-xs font-bold text-white shadow`}>
        {category} Risk
      </span>
    </div>
  );
}
