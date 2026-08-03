import { useState } from 'react';

interface BookingFormData {
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
  booking_changes: number;
  total_of_special_requests: number;
  required_car_parking_spaces: number;
  days_in_waiting_list: number;
  room_mismatch: boolean;
  current_occupancy_rate: number;
}

interface BookingFormProps {
  onSubmit: (data: BookingFormData) => void;
  loading: boolean;
}

const DEFAULTS: BookingFormData = {
  hotel_type: 'City Hotel',
  lead_time: 30,
  arrival_month: 7,
  total_nights: 3,
  total_guests: 2,
  market_segment: 'Online TA',
  distribution_channel: 'TA/TO',
  customer_type: 'Transient',
  deposit_type: 'No Deposit',
  meal: 'BB',
  country: 'PRT',
  is_repeated_guest: false,
  previous_cancellations: 0,
  previous_bookings_not_canceled: 0,
  booking_changes: 0,
  total_of_special_requests: 1,
  required_car_parking_spaces: 0,
  days_in_waiting_list: 0,
  room_mismatch: false,
  current_occupancy_rate: 0.6,
};

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export default function BookingForm({ onSubmit, loading }: BookingFormProps) {
  const [form, setForm] = useState<BookingFormData>(DEFAULTS);

  const set = <K extends keyof BookingFormData>(key: K, value: BookingFormData[K]) =>
    setForm(prev => ({ ...prev, [key]: value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  const inputClass = "w-full rounded-lg border border-slate-600 bg-slate-700/50 px-3 py-2 text-sm text-slate-100 placeholder-slate-400 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition";
  const labelClass = "block text-xs font-medium text-slate-300 mb-1";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Row 1 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className={labelClass}>Hotel Type</label>
          <select value={form.hotel_type} onChange={e => set('hotel_type', e.target.value)} className={inputClass}>
            <option>City Hotel</option>
            <option>Resort Hotel</option>
          </select>
        </div>
        <div>
          <label className={labelClass}>Lead Time (days)</label>
          <input type="number" min={0} value={form.lead_time} onChange={e => set('lead_time', +e.target.value)} className={inputClass} />
        </div>
        <div>
          <label className={labelClass}>Arrival Month</label>
          <select value={form.arrival_month} onChange={e => set('arrival_month', +e.target.value)} className={inputClass}>
            {MONTHS.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
          </select>
        </div>
        <div>
          <label className={labelClass}>Occupancy Rate</label>
          <input type="number" min={0} max={1} step={0.05} value={form.current_occupancy_rate} onChange={e => set('current_occupancy_rate', +e.target.value)} className={inputClass} />
        </div>
      </div>

      {/* Row 2 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className={labelClass}>Total Nights</label>
          <input type="number" min={1} value={form.total_nights} onChange={e => set('total_nights', +e.target.value)} className={inputClass} />
        </div>
        <div>
          <label className={labelClass}>Total Guests</label>
          <input type="number" min={1} value={form.total_guests} onChange={e => set('total_guests', +e.target.value)} className={inputClass} />
        </div>
        <div>
          <label className={labelClass}>Market Segment</label>
          <select value={form.market_segment} onChange={e => set('market_segment', e.target.value)} className={inputClass}>
            {[
              { val: 'Direct', label: 'Direct' },
              { val: 'Corporate', label: 'Corporate' },
              { val: 'Online TA', label: 'Online Travel Agency (Online TA)' },
              { val: 'Offline TA/TO', label: 'Offline Travel Agency / Tour Operator' },
              { val: 'Complementary', label: 'Complementary' },
              { val: 'Groups', label: 'Groups' },
              { val: 'Aviation', label: 'Aviation' }
            ].map(o => <option key={o.val} value={o.val}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label className={labelClass}>Distribution Channel</label>
          <select value={form.distribution_channel} onChange={e => set('distribution_channel', e.target.value)} className={inputClass}>
            {[
              { val: 'Direct', label: 'Direct' },
              { val: 'Corporate', label: 'Corporate' },
              { val: 'TA/TO', label: 'Travel Agency / Tour Operator (TA/TO)' },
              { val: 'GDS', label: 'Global Distribution System (GDS)' },
              { val: 'Undefined', label: 'Undefined' }
            ].map(o => <option key={o.val} value={o.val}>{o.label}</option>)}
          </select>
        </div>
      </div>

      {/* Row 3 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className={labelClass}>Customer Type</label>
          <select value={form.customer_type} onChange={e => set('customer_type', e.target.value)} className={inputClass}>
            {['Transient', 'Contract', 'Transient-Party', 'Group'].map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className={labelClass}>Deposit Type</label>
          <select value={form.deposit_type} onChange={e => set('deposit_type', e.target.value)} className={inputClass}>
            {['No Deposit', 'Refundable', 'Non Refund'].map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className={labelClass}>Meal</label>
          <select value={form.meal} onChange={e => set('meal', e.target.value)} className={inputClass}>
            {[
              { val: 'BB', label: 'Bed & Breakfast (BB)' },
              { val: 'HB', label: 'Half Board (HB)' },
              { val: 'FB', label: 'Full Board (FB)' },
              { val: 'SC', label: 'Self Catering (SC)' },
              { val: 'Undefined', label: 'Undefined' }
            ].map(o => <option key={o.val} value={o.val}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label className={labelClass}>Country</label>
          <input type="text" value={form.country} onChange={e => set('country', e.target.value)} placeholder="ISO code" className={inputClass} />
        </div>
      </div>

      {/* Row 4 — toggles & small numbers */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className={labelClass}>Prev. Cancellations</label>
          <input type="number" min={0} value={form.previous_cancellations} onChange={e => set('previous_cancellations', +e.target.value)} className={inputClass} />
        </div>
        <div>
          <label className={labelClass}>Prev. Bookings (kept)</label>
          <input type="number" min={0} value={form.previous_bookings_not_canceled} onChange={e => set('previous_bookings_not_canceled', +e.target.value)} className={inputClass} />
        </div>
        <div>
          <label className={labelClass}>Special Requests</label>
          <input type="number" min={0} value={form.total_of_special_requests} onChange={e => set('total_of_special_requests', +e.target.value)} className={inputClass} />
        </div>
        <div>
          <label className={labelClass}>Booking Changes</label>
          <input type="number" min={0} value={form.booking_changes} onChange={e => set('booking_changes', +e.target.value)} className={inputClass} />
        </div>
      </div>

      {/* Row 5 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 items-end">
        <div>
          <label className={labelClass}>Parking Spaces</label>
          <input type="number" min={0} value={form.required_car_parking_spaces} onChange={e => set('required_car_parking_spaces', +e.target.value)} className={inputClass} />
        </div>
        <div>
          <label className={labelClass}>Waiting List Days</label>
          <input type="number" min={0} value={form.days_in_waiting_list} onChange={e => set('days_in_waiting_list', +e.target.value)} className={inputClass} />
        </div>
        <div className="flex items-center gap-3 pt-5">
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" checked={form.is_repeated_guest} onChange={e => set('is_repeated_guest', e.target.checked)} className="sr-only peer" />
            <div className="w-9 h-5 bg-slate-600 rounded-full peer peer-checked:bg-indigo-500 transition after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-full"></div>
            <span className="ml-2 text-xs text-slate-300">Repeat Guest</span>
          </label>
        </div>
        <div className="flex items-center gap-3 pt-5">
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" checked={form.room_mismatch} onChange={e => set('room_mismatch', e.target.checked)} className="sr-only peer" />
            <div className="w-9 h-5 bg-slate-600 rounded-full peer peer-checked:bg-amber-500 transition after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-full"></div>
            <span className="ml-2 text-xs text-slate-300">Room Mismatch</span>
          </label>
        </div>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-3 text-sm font-semibold text-white shadow-lg hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 transition-all duration-200 cursor-pointer"
      >
        {loading ? 'Analysing…' : '✨  Get Price Recommendation'}
      </button>
    </form>
  );
}
