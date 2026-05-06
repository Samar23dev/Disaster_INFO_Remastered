import { Sun, Moon, Bell, Activity } from 'lucide-react';
import { useTheme } from '../hooks/useTheme';

export default function TopBar() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="h-16 glass sticky top-0 z-20 flex items-center justify-between px-6">
      <div className="flex text-lg font-semibold items-center md:hidden">
         <span className="text-primary mr-2">GeoPulse</span>
      </div>
      <div className="hidden md:flex flex-1 items-center space-x-2 text-sm text-textMuted font-medium">
         <Activity className="w-4 h-4 text-success animate-pulse" />
         <span>System Online</span>
      </div>

      <div className="flex items-center space-x-4">
        <button 
          onClick={toggleTheme}
          className="p-2 rounded-full hover:bg-surfaceBorder/50 transition-colors"
          aria-label="Toggle Theme"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5 text-warning" /> : <Moon className="w-5 h-5 text-primary" />}
        </button>
        <button className="p-2 rounded-full hover:bg-surfaceBorder/50 transition-colors relative">
          <Bell className="w-5 h-5 text-textMain" />
          <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-danger rounded-full border-2 border-surface"></span>
        </button>
      </div>
    </header>
  );
}
