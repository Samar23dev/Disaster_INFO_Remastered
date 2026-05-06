import { useEffect, useState } from 'react';
import { getStats } from '../api/client';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function Analytics() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    getStats().then(setStats).catch(console.error);
  }, []);

  const typeData = Object.entries(stats?.by_type || {}).map(([name, value]) => ({ name, value }));
  const severityData = Object.entries(stats?.by_severity || {}).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-primaryHover bg-clip-text text-transparent">Analytics</h1>
        <p className="text-textMuted mt-1">Data breakdown by classification and severity.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[400px]">
        <div className="glass rounded-xl p-6 flex flex-col">
          <h2 className="text-lg font-bold mb-4 border-b border-surfaceBorder pb-2">Events by Type</h2>
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeData}>
                <XAxis dataKey="name" stroke="#64748b" tick={{fill: '#64748b'}} />
                <YAxis stroke="#64748b" tick={{fill: '#64748b'}} />
                <Tooltip cursor={{fill: 'transparent'}} contentStyle={{backgroundColor: 'var(--surface)', borderColor: 'var(--surface-border)', color: 'var(--text-main)'}} />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass rounded-xl p-6 flex flex-col">
          <h2 className="text-lg font-bold mb-4 border-b border-surfaceBorder pb-2">Severity Distribution</h2>
          <div className="flex-1 min-h-0 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={
                        entry.name === 'HIGH' ? '#ef4444' : 
                        entry.name === 'MEDIUM' ? '#f59e0b' : '#10b981'
                    } />
                  ))}
                </Pie>
                <Tooltip contentStyle={{backgroundColor: 'var(--surface)', borderColor: 'var(--surface-border)', color: 'var(--text-main)'}} />
                <Legend iconType="circle" wrapperStyle={{color: 'var(--text-main)'}}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
