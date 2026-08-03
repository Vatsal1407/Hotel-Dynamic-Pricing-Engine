import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Recommender from './pages/Recommender';
import History from './pages/History';
import About from './pages/About';

const navItems = [
  { to: '/', label: '✨ Recommender' },
  { to: '/history', label: '📋 History' },
  { to: '/about', label: 'ℹ️ About' },
];

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
        {/* Navigation */}
        <nav className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/80 backdrop-blur-xl">
          <div className="mx-auto max-w-6xl flex items-center justify-between px-6 py-3">
            <div className="flex items-center gap-2">
              <span className="text-xl">🏨</span>
              <span className="text-base font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                Hotel Pricing Engine
              </span>
            </div>
            <div className="flex gap-1">
              {navItems.map(({ to, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-indigo-600/20 text-indigo-300 shadow-inner'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`
                  }
                >
                  {label}
                </NavLink>
              ))}
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main className="mx-auto max-w-6xl px-6 py-8">
          <Routes>
            <Route path="/" element={<Recommender />} />
            <Route path="/history" element={<History />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800 mt-16">
          <div className="mx-auto max-w-6xl px-6 py-6 flex flex-col md:flex-row items-center justify-between text-xs text-slate-500">
            <p>Hotel Dynamic Pricing Engine — Built with XGBoost, FastAPI &amp; React</p>
            <p className="mt-2 md:mt-0">
              ⚠️ Uses correlational patterns, not experimental price-elasticity data.
            </p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}
