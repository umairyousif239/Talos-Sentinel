import { useEffect, useState } from "react";

const API = "http://127.0.0.1:8000";

function Card({ title, children }) {
  return (
    <div className="bg-gray-800 rounded-xl p-5 shadow-lg">
      <h2 className="text-lg font-semibold mb-3 text-gray-200">{title}</h2>
      {children}
    </div>
  );
}

function Freshness({ timestamp }) {
  const [age, setAge] = useState(0);

  useEffect(() => {
    if (!timestamp) return;

    const updateAge = () => {
      setAge(Date.now() - new Date(timestamp).getTime());
    };

    updateAge();
    const interval = setInterval(updateAge, 1000);
    return () => clearInterval(interval);
  }, [timestamp]);

  if (!timestamp) return <span className="text-red-500">●</span>;

  let color = "text-red-500";
  if (age < 1000) color = "text-green-400";
  else if (age < 5000) color = "text-yellow-400";

  return (
    <span className={`${color}`}>
      ● {Math.round(age / 1000)}s
    </span>
  );
}

export default function App() {
  const [sensor, setSensor] = useState(null);
  const [vision, setVision] = useState(null);
  const [alert, setAlert] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const fetchData = () => {
      fetch(`${API}/sensors/latest`)
        .then(r => r.json())
        .then(setSensor)
        .catch(() => setSensor(null));

      fetch(`${API}/vision/latest`)
        .then(r => r.json())
        .then(setVision)
        .catch(() => setVision(null));

      fetch(`${API}/alerts/latest`)
        .then(r => r.json())
        .then(setAlert)
        .catch(() => setAlert(null));

      fetch(`${API}/alerts/history`)
        .then(r => r.json())
        .then(setHistory)
        .catch(() => setHistory([]));
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <h1 className="text-3xl font-bold mb-8">🔥 Fire Detection Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Sensors */}
        <Card title="Sensors">
          {sensor ? (
            <div className="space-y-2">
              <p>Flame: {sensor.flame ? "🔥 DETECTED" : "No flame"}</p>
              <p>MQ135: {sensor.mq135_raw}</p>
              <p>
                Thermal Max:{" "}
                {sensor.thermal
                  ? Math.max(...sensor.thermal).toFixed(2)
                  : "N/A"}
              </p>
              <p>
                Updated: <Freshness timestamp={sensor.timestamp} />
              </p>
            </div>
          ) : (
            <p>No sensor data</p>
          )}
        </Card>

        {/* Vision */}
        <Card title="Vision">
          {vision ? (
            <div className="space-y-2">
              <p>
                Fire Detected: {vision.detected ? "🔥 YES" : "No"}
              </p>
              <p>Confidence: {vision.confidence}</p>
              <p>
                Updated: <Freshness timestamp={vision.timestamp} />
              </p>
            </div>
          ) : (
            <p>No vision data</p>
          )}
        </Card>

        {/* Current Alert */}
        <Card title="Current Alert">
          {alert && alert.status !== "NO_ALERT" ? (
            <div className="space-y-2">
              <p>Status: {alert.status}</p>
              <p>Type: {alert.type}</p>
              <p>Source: {alert.source}</p>
              <p>Confidence: {alert.confidence}</p>
              <p>
                Updated: <Freshness timestamp={alert.updated_at} />
              </p>
            </div>
          ) : (
            <p>No active alert</p>
          )}
        </Card>

        {/* Alert History */}
        <Card title="Alert History">
          {history.length > 0 ? (
            <ul className="space-y-1 text-sm">
              {history.slice(0, 5).map((a, i) => (
                <li key={i} className="border-b border-gray-700 pb-1">
                  {a.type} | {a.status}
                </li>
              ))}
            </ul>
          ) : (
            <p>No alerts yet</p>
          )}
        </Card>

      </div>
    </div>
  );
}
