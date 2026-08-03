export default function About() {
  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
          About This System
        </h1>
        <p className="text-slate-400 mt-1 text-sm">
          How the pricing engine works, model metrics, and honest limitations.
        </p>
      </div>

      {/* Methodology */}
      <section className="rounded-2xl border border-slate-700 bg-slate-800/60 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-slate-100">Methodology</h2>
        <p className="text-sm text-slate-300 leading-relaxed">
          This system uses an <strong className="text-indigo-300">XGBoost cancellation prediction model</strong> trained
          on the <em>Hotel Booking Demand</em> dataset (Antonio, Almeida &amp; Nunes, 2019 — ~119 k bookings across
          two Portuguese hotels). The model predicts the probability that a booking will be cancelled given its
          characteristics.
        </p>
        <p className="text-sm text-slate-300 leading-relaxed">
          For price recommendations, the system performs a{' '}
          <strong className="text-indigo-300">counterfactual ADR sweep</strong>: it holds all booking features constant
          except the Average Daily Rate (ADR), evaluates predicted cancellation probability at each price point, and
          computes <code className="text-xs bg-slate-700 px-1.5 py-0.5 rounded">expected_revenue = price × (1 − p_cancel)</code>.
          The price that maximises expected revenue — subject to occupancy-pacing constraints — is recommended.
        </p>
      </section>

      {/* Honesty Disclaimer */}
      <section className="rounded-2xl border border-amber-800/50 bg-amber-950/30 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-amber-300">⚠️ Honest Limitations</h2>
        <ul className="text-sm text-slate-300 space-y-3 list-disc list-inside">
          <li>
            <strong className="text-amber-200">No experimental price-elasticity data.</strong>{' '}
            The "price response curve" reflects correlational patterns in historical cancellations, not true
            experimentally-measured demand elasticity. It is a form of partial-dependence / what-if analysis
            on a trained supervised model.
          </li>
          <li>
            <strong className="text-amber-200">Two-hotel dataset.</strong>{' '}
            Trained on data from two Portuguese hotels — it should not be assumed to generalise to all
            markets, geographies, or hotel types without retraining.
          </li>
          <li>
            <strong className="text-amber-200">No real-time demand signal.</strong>{' '}
            The model has no access to live competitor prices, market demand forecasts, or event calendars.
          </li>
          <li>
            <strong className="text-amber-200">Occupancy-pacing is rule-based.</strong>{' '}
            The constraint bands (near-sellout, low-occupancy) are hand-tuned heuristics, not learned parameters.
          </li>
        </ul>
      </section>

      {/* Model Metrics */}
      <section className="rounded-2xl border border-slate-700 bg-slate-800/60 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-slate-100">Model Metrics (Temporal Test Set)</h2>
        <p className="text-xs text-slate-400">
          Evaluated on a held-out 15% temporal split (chronologically last bookings — the model never saw these during training).
        </p>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-3">
          {[
            ['Accuracy', '72.8%'],
            ['Precision', '58.0%'],
            ['Recall', '73.5%'],
            ['F1-Score', '64.8%'],
            ['ROC-AUC', '81.5%'],
          ].map(([label, value]) => (
            <div key={label} className="text-center rounded-xl bg-slate-700/40 p-3">
              <p className="text-lg font-bold text-indigo-300">{value}</p>
              <p className="text-xs text-slate-400 mt-1">{label}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Trained on 60,996 bookings | scale_pos_weight imbalance handling | Optuna-tuned (30 trials, ROC-AUC objective) | Early stopping | Threshold tuned on val set | Temporal test set: 13,071 bookings
        </p>
      </section>

      {/* Tech Stack */}
      <section className="rounded-2xl border border-slate-700 bg-slate-800/60 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-slate-100">Tech Stack</h2>
        <div className="grid grid-cols-2 gap-3 text-sm">
          {[
            ['ML Model', 'XGBoost (binary classification)'],
            ['Feature Engineering', '39 features (temporal, guest, pricing, interactions)'],
            ['Balancing', 'XGBoost scale_pos_weight (Optuna-tuned, no SMOTE)'],
            ['Hyperparameters', 'Optuna TPE sampler (30 trials, ROC-AUC objective)'],
            ['Early Stopping', 'XGBoost EarlyStopping (50 rounds on final model)'],
            ['Threshold', 'Val-set F1-optimal threshold (0.495 vs default 0.5)'],
            ['Backend', 'FastAPI + SQLAlchemy + PostgreSQL'],
            ['Frontend', 'React + Vite + TypeScript + Tailwind + Recharts'],
            ['Deployment', 'Docker Compose (local) / Render + Neon (cloud)'],
          ].map(([k, v]) => (
            <div key={k} className="flex gap-2">
              <span className="text-slate-400 font-medium min-w-[140px]">{k}</span>
              <span className="text-slate-300">{v}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Resume Bullet */}
      <section className="rounded-2xl border border-slate-700 bg-slate-800/60 p-6 space-y-3">
        <h2 className="text-lg font-semibold text-slate-100">📝 Resume Bullet</h2>
        <blockquote className="border-l-4 border-indigo-500 pl-4 text-sm text-slate-300 italic leading-relaxed">
          "Built a cancellation-risk-aware dynamic pricing engine for hotels using XGBoost (39 engineered features,
          temporal train/test split, Optuna). FastAPI backend serves counterfactual price-response curves;
          React + Recharts dashboard visualises recommendations under occupancy-pacing constraints."
        </blockquote>
      </section>
    </div>
  );
}
