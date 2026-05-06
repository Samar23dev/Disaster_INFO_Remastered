import { useEffect, useState } from 'react';
import { getStats, getEvents } from '../api/client';
import StatCard from '../components/StatCard';
import PulseButton from '../components/PulseButton';
import { Activity, AlertTriangle, ShieldAlert, FileText, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [_stats, _events] = await Promise.all([
        getStats(),
        getEvents({ limit: 5 })
      ]);
      setStats(_stats);
      setRecentEvents(_events.events || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000); // refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) {
    return <div className="flex h-full items-center justify-center"><Activity className="w-8 h-8 animate-spin text-primary" /></div>;
  }

  const highSeverity = stats?.by_severity?.HIGH || 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-primaryHover bg-clip-text text-transparent">Live Dashboard</h1>
          <p className="text-textMuted mt-1">Real-time overview of disaster intelligence in India.</p>
        </div>
        <PulseButton onTrigger={loadData} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Processed Events" 
          value={stats?.total_events || 0} 
          icon={Activity} 
          pulse={true}
        />
        <StatCard 
          title="High Severity Events" 
          value={highSeverity} 
          valueColor={highSeverity > 0 ? "text-danger" : "text-success"}
          icon={AlertTriangle} 
        />
        <StatCard 
          title="Pending Raw Feeds" 
          value={stats?.raw_pending || 0} 
          icon={FileText} 
        />
        <StatCard 
          title="Active Alerts" 
          value={stats?.alerts || 0} 
          icon={ShieldAlert} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass rounded-xl p-6">
           <div className="flex justify-between items-center mb-6 border-b border-surfaceBorder pb-4">
              <h2 className="text-xl font-bold">Recent Events Flow</h2>
              <Link to="/events" className="text-primary text-sm font-medium hover:underline flex items-center">
                View All <ChevronRight className="w-4 h-4 ml-1" />
              </Link>
           </div>
           
           <div className="space-y-4">
             {recentEvents.length === 0 ? (
               <p className="text-textMuted text-center py-8">No recent events detected.</p>
             ) : (
               recentEvents.map(ev => (
                 <div key={ev._id} className="flex justify-between items-start p-4 rounded-lg bg-background border border-surfaceBorder hover:border-primary/30 transition-colors">
                   <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-bold uppercase tracking-wide
                          ${ev.severity === 'HIGH' ? 'bg-red-500/20 text-danger' : 
                            ev.severity === 'MEDIUM' ? 'bg-amber-500/20 text-warning' : 'bg-emerald-500/20 text-success'}`}>
                          {ev.severity}
                        </span>
                        <span className="text-sm font-semibold capitalize text-textMain">{ev.disaster_type}</span>
                      </div>
                      <p className="font-medium text-lg leading-tight mt-1">{ev.location?.name || 'Unknown Location'}</p>
                      <p className="text-xs text-textMuted mt-1">{new Date(ev.timestamp).toLocaleString()}</p>
                   </div>
                   <div className="text-right flex flex-col items-end">
                      <span className="text-xs text-textMuted bg-surface px-2 py-1 rounded">Conf: {(ev.confidence * 100).toFixed(0)}%</span>
                      <span className="text-xs mt-1 font-mono text-textMuted">{ev.source}</span>
                   </div>
                 </div>
               ))
             )}
           </div>
        </div>

        <div className="glass rounded-xl p-6">
          <h2 className="text-xl font-bold mb-6 border-b border-surfaceBorder pb-4">Events by Type</h2>
          <div className="space-y-4">
            {Object.entries(stats?.by_type || {}).sort((a,b)=>b[1]-a[1]).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between">
                <span className="capitalize font-medium">{type}</span>
                <span className="bg-blue-500/20 text-primary w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
