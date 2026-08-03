import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ── Types ───────────────────────────────────────────────────────────────────

export interface CancellationRiskRequest {
  hotel_type: string;
  lead_time: number;
  arrival_month: number;
  total_nights: number;
  total_guests: number;
  market_segment: string;
  distribution_channel: string;
  customer_type: string;
  deposit_type: string;
  meal: string;
  country: string;
  adr: number;
  is_repeated_guest: boolean;
  previous_cancellations: number;
  previous_bookings_not_canceled: number;
  booking_changes?: number;
  total_of_special_requests?: number;
  required_car_parking_spaces?: number;
  days_in_waiting_list?: number;
  room_mismatch?: boolean;
}

export interface CancellationRiskResponse {
  cancellation_probability: number;
  risk_category: string;
}

export interface RecommendPriceRequest {
  hotel_type: string;
  lead_time: number;
  arrival_month: number;
  total_nights: number;
  total_guests: number;
  market_segment: string;
  distribution_channel: string;
  customer_type: string;
  deposit_type: string;
  meal: string;
  country: string;
  is_repeated_guest: boolean;
  previous_cancellations: number;
  previous_bookings_not_canceled: number;
  booking_changes?: number;
  total_of_special_requests?: number;
  required_car_parking_spaces?: number;
  days_in_waiting_list?: number;
  room_mismatch?: boolean;
  current_occupancy_rate: number;
}

export interface PriceCurvePoint {
  price: number;
  expected_revenue: number;
  cancellation_probability: number;
}

export interface RecommendPriceResponse {
  recommended_price: number;
  price_multiplier: number;
  expected_revenue: number;
  cancellation_probability_at_recommended_price: number;
  constraint_applied: string;
  price_curve: PriceCurvePoint[];
}

export interface HistoryItem {
  id: number;
  created_at: string;
  input_payload: Record<string, unknown>;
  recommended_price: number | null;
  expected_revenue: number | null;
  cancellation_probability: number | null;
  occupancy_rate: number | null;
}

// ── API calls ───────────────────────────────────────────────────────────────

export async function getCancellationRisk(data: CancellationRiskRequest) {
  const res = await api.post<CancellationRiskResponse>('/predict/cancellation-risk', data);
  return res.data;
}

export async function getRecommendedPrice(data: RecommendPriceRequest) {
  const res = await api.post<RecommendPriceResponse>('/predict/recommend-price', data);
  return res.data;
}

export async function getHistory(limit = 50) {
  const res = await api.get<HistoryItem[]>('/history', { params: { limit } });
  return res.data;
}

export default api;
