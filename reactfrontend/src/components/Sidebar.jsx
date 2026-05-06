import { NavLink } from 'react-router-dom';
import { Home, List, Map, BarChart2 } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: Home },
  { path: '/events', label: 'Events Feed', icon: List },
  { path: '/map', label: 'Map Explorer', icon: Map },
  { path: '/analytics', label: 'Analytics', icon: BarChart2 },
];

export default function Sidebar() {
  return (
    <aside className="w-64 glass hidden md:flex flex-col h-full z-10 sticky top-0">
      <div className="p-6">
        <h1 className="text-2xl font-bold tracking-wider text-primary">GeoPulse</h1>
        <p className="text-xs text-textMuted uppercase tracking-widest mt-1 font-semibold">Intelligence</p>
      </div>
      <nav className="flex-1 mt-6 px-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center px-4 py-3 text-sm rounded-lg transition-all duration-200 group ${
                  isActive
                    ? 'bg-primary/10 text-primary font-semibold'
                    : 'text-textMuted hover:bg-surfaceBorder/50 hover:text-textMain'
                }`
              }
            >
              <Icon className="w-5 h-5 mr-3 transition-transform group-hover:scale-110" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
      <div className="p-4 border-t border-surfaceBorder/50 mt-auto">
        <div className="text-xs text-textMuted text-center">
          Monitoring India Real-Time
        </div>
      </div>
    </aside>
  );
}
