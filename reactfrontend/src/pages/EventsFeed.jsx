import { useEffect, useState } from 'react';
import { getEvents } from '../api/client';
import { Filter } from 'lucide-react';

export default function EventsFeed() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');

  const loadEvents = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterType) params.disaster_type = filterType;
      if (filterSeverity) params.severity = filterSeverity;
      params.limit = 50;

      const data = await getEvents(params);
      setEvents(data.events || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [filterType, filterSeverity]);

  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-primaryHover bg-clip-text text-transparent">Events Feed</h1>
          <p className="text-textMuted mt-1">Comprehensive list of all tracked incidents.</p>
        </div>
        
        <div className="flex gap-4 items-center bg-surface p-2 rounded-lg border border-surfaceBorder">
           <Filter className="w-5 h-5 text-textMuted ml-2" />
           <select 
             className="bg-transparent border-none text-sm outline-none focus:ring-0 cursor-pointer"
             value={filterType}
             onChange={e => setFilterType(e.target.value)}
           >
             <option value="">All Types</option>
             <option value="flood">Flood</option>
             <option value="earthquake">Earthquake</option>
             <option value="fire">Fire</option>
             <option value="storm">Storm</option>
             <option value="landslide">Landslide</option>
           </select>
           
           <div className="w-px h-6 bg-surfaceBorder"></div>

           <select 
             className="bg-transparent border-none text-sm outline-none focus:ring-0 cursor-pointer pr-2"
             value={filterSeverity}
             onChange={e => setFilterSeverity(e.target.value)}
           >
             <option value="">All Severities</option>
             <option value="HIGH">High</option>
             <option value="MEDIUM">Medium</option>
             <option value="LOW">Low</option>
           </select>
        </div>
      </div>

      <div className="flex-1 overflow-auto bg-surface rounded-xl border border-surfaceBorder overflow-hidden">
         {loading ? (
           <div className="p-8 text-center text-textMuted animate-pulse">Loading events...</div>
         ) : events.length === 0 ? (
           <div className="p-8 text-center text-textMuted">No events match your criteria.</div>
         ) : (
           <table className="w-full text-left border-collapse">
             <thead>
               <tr className="bg-background border-b border-surfaceBorder text-xs uppercase tracking-wider text-textMuted">
                 <th className="p-4 font-semibold">Severity</th>
                 <th className="p-4 font-semibold">Type</th>
                 <th className="p-4 font-semibold">Location</th>
                 <th className="p-4 font-semibold">Time</th>
               </tr>
             </thead>
             <tbody className="divide-y divide-surfaceBorder">
               {events.map((ev) => (
                 <tr key={ev._id} className="hover:bg-background/50 transition-colors">
                   <td className="p-4">
                     <span className={`text-xs px-2 py-1 rounded-full font-bold uppercase tracking-wide
                        ${ev.severity === 'HIGH' ? 'bg-red-500/20 text-danger' : 
                          ev.severity === 'MEDIUM' ? 'bg-amber-500/20 text-warning' : 'bg-emerald-500/20 text-success'}`}>
                        {ev.severity}
                     </span>
                   </td>
                   <td className="p-4 font-medium capitalize text-primary">{ev.disaster_type}</td>
                   <td className="p-4">{ev.location?.name || 'Unknown'}</td>
                   <td className="p-4 text-sm text-textMuted">{new Date(ev.timestamp).toLocaleString()}</td>
                 </tr>
               ))}
             </tbody>
           </table>
         )}
      </div>
    </div>
  );
}
