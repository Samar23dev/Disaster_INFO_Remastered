import { useState } from 'react';
import { Activity } from 'lucide-react';
import { triggerPipeline } from '../api/client';

export default function PulseButton({ onTrigger }) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      await triggerPipeline();
      if(onTrigger) onTrigger();
    } catch (e) {
      console.error(e);
    }
    setTimeout(() => {
      setLoading(false);
    }, 1500); // Visual feedback
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className={`px-4 py-2 rounded-lg font-medium shadow-sm transition-all flex items-center ${
        loading 
          ? 'bg-surfaceBorder text-textMuted cursor-not-allowed' 
          : 'bg-primary text-white hover:bg-primaryHover hover:shadow-md active:scale-95'
      }`}
    >
      <Activity className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
      {loading ? 'Pipeline Running...' : 'Force Pipeline Run'}
    </button>
  );
}
