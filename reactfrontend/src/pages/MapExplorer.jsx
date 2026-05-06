import { useEffect, useState } from 'react';
import { getHeatmap } from '../api/client';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useTheme } from '../hooks/useTheme';

export default function MapExplorer() {
  const [points, setPoints] = useState([]);
  const { theme } = useTheme();

  useEffect(() => {
    getHeatmap().then(data => setPoints(data.points || [])).catch(console.error);
  }, []);

  // Standard OpenStreetMap for light, CartoDB Dark Matter for dark
  const tileUrl = theme === 'dark' 
    ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
    : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

  return (
    <div className="flex flex-col h-full space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-primaryHover bg-clip-text text-transparent">Map Explorer</h1>
        <p className="text-textMuted mt-1">Spatial distribution of disaster events.</p>
      </div>
      
      <div className="flex-1 rounded-xl overflow-hidden border border-surfaceBorder shadow-inner relative z-0">
        <MapContainer center={[22.3511, 78.6677]} zoom={5} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            url={tileUrl}
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          {points.map((pt, idx) => {
            const isHigh = pt.weight >= 3;
            const isMedium = pt.weight === 2;
            return (
              <CircleMarker
                key={idx}
                center={[pt.lat, pt.lon]}
                radius={isHigh ? 12 : isMedium ? 8 : 5}
                fillColor={isHigh ? "#ef4444" : isMedium ? "#f59e0b" : "#3b82f6"}
                color={isHigh ? "#ef4444" : isMedium ? "#f59e0b" : "#3b82f6"}
                fillOpacity={0.6}
                weight={1}
              >
                <Popup>
                  <div className="p-1">
                    <p className="font-semibold text-textMain capitalize">Severity Weight: {pt.weight}</p>
                    <p className="text-sm text-textMuted">Lat: {pt.lat.toFixed(2)}, Lon: {pt.lon.toFixed(2)}</p>
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>
      </div>
    </div>
  );
}
