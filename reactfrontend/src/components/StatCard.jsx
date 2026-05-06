export default function StatCard({ title, value, subtitle, icon, valueColor = "text-textMain", pulse = false }) {
  const Icon = icon;
  
  return (
    <div className="glass rounded-xl p-6 transition-all hover:shadow-lg hover:-translate-y-1 relative overflow-hidden group">
      <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
         {Icon && <Icon className="w-24 h-24 transform translate-x-4 -translate-y-4" />}
      </div>
      
      <div className="relative z-10 flex flex-col h-full">
        <h3 className="text-sm font-semibold text-textMuted uppercase tracking-wider mb-2 flex items-center">
          {title}
          {pulse && <span className="ml-2 w-2 h-2 rounded-full bg-success animate-pulse inline-block"></span>}
        </h3>
        
        <div className={`text-4xl font-bold mb-1 ${valueColor}`}>
          {value}
        </div>
        
        {subtitle && (
          <p className="text-sm text-textMuted mt-auto font-medium">
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
}
