interface Props {
  recommendedPrice: number;
  priceMultiplier: number;
  expectedRevenue: number;
  constraintApplied: string;
}

export default function RecommendationCard({ recommendedPrice, priceMultiplier, expectedRevenue, constraintApplied }: Props) {
  const multiplierColor = priceMultiplier >= 1.1
    ? 'text-emerald-400'
    : priceMultiplier <= 0.9
      ? 'text-rose-400'
      : 'text-slate-200';

  return (
    <div className="rounded-2xl border border-slate-700 bg-gradient-to-br from-slate-800/80 to-slate-900/80 p-6 shadow-xl backdrop-blur">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-4">
        Price Recommendation
      </h3>

      <div className="grid grid-cols-3 gap-4 mb-5">
        <div className="text-center">
          <p className="text-3xl font-bold text-white">${recommendedPrice.toFixed(2)}</p>
          <p className="text-xs text-slate-400 mt-1">Recommended Price</p>
        </div>
        <div className="text-center">
          <p className={`text-3xl font-bold ${multiplierColor}`}>{priceMultiplier.toFixed(2)}×</p>
          <p className="text-xs text-slate-400 mt-1">Price Multiplier</p>
        </div>
        <div className="text-center">
          <p className="text-3xl font-bold text-amber-300">${expectedRevenue.toFixed(2)}</p>
          <p className="text-xs text-slate-400 mt-1">Expected Revenue</p>
        </div>
      </div>

      <div className="rounded-lg bg-slate-700/40 px-4 py-2.5 text-xs text-slate-300">
        <span className="font-medium text-slate-200">Constraint: </span>
        {constraintApplied}
      </div>
    </div>
  );
}
