import { useState } from 'react';
import BookingForm from '../components/BookingForm';
import RecommendationCard from '../components/RecommendationCard';
import RiskGauge from '../components/RiskGauge';
import PriceCurveChart from '../components/PriceCurveChart';
import { getRecommendedPrice, type RecommendPriceResponse } from '../api/client';

export default function Recommender() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecommendPriceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleSubmit = async (formData: any) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await getRecommendedPrice(formData);
      setResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Something went wrong';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
          Price Recommender
        </h1>
        <p className="text-slate-400 mt-1 text-sm">
          Enter booking details to receive a revenue-optimised price recommendation.
        </p>
      </div>

      {/* Form card */}
      <div className="rounded-2xl border border-slate-700 bg-slate-800/60 p-6 shadow-xl backdrop-blur">
        <BookingForm onSubmit={handleSubmit} loading={loading} />
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl bg-rose-950/40 border border-rose-800 p-4 text-sm text-rose-300">
          ⚠️ {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6 animate-in fade-in duration-500">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <RecommendationCard
                recommendedPrice={result.recommended_price}
                priceMultiplier={result.price_multiplier}
                expectedRevenue={result.expected_revenue}
                constraintApplied={result.constraint_applied}
              />
            </div>
            <div>
              <RiskGauge probability={result.cancellation_probability_at_recommended_price} />
            </div>
          </div>

          <PriceCurveChart
            curve={result.price_curve}
            recommendedPrice={result.recommended_price}
          />
        </div>
      )}
    </div>
  );
}
