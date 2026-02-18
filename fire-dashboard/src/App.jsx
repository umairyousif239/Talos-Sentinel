import { useEffect, useState } from "react";

const API = "http://127.0.0.1:8000";

/* ================= CARD COMPONENT ================= */

function Card({ title, children, className = "" }) {
  return (
    <div
      className={`bg-gray-800 rounded-2xl p-6 shadow-xl border border-gray-700 ${className}`}
    >
      <h2 className="text-lg font-semibold mb-4 text-gray-200">
        {title}
      </h2>
      {children}
    </div>
  );
}

/* ================= DATA FRESHNESS INDICATOR ================= */

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
    <span className={`${color} font-medium`}>
      ● {Math.round(age / 1000)}s
    </span>
  );
}

/* ================= THERMAL GRID ================= */

function ThermalGrid({ data }) {
  if (!data || data.length !== 64) {
    return <p>No thermal data</p>;
  }

  // 🔥 Fixed temperature scale
  const MIN_TEMP = 20;   // lowest expected ambient
  const MAX_TEMP = 50;   // fire-relevant upper bound

  const clamp = (val, min, max) => Math.min(Math.max(val, min), max);

  const normalize = (value) => {
    const clamped = clamp(value, MIN_TEMP, MAX_TEMP);
    return (clamped - MIN_TEMP) / (MAX_TEMP - MIN_TEMP);
  };

  return (
    <div className="flex items-start gap-6">

      {/* 8x8 Thermal Grid */}
      <div className="w-64 h-64 grid grid-cols-8 rounded-lg overflow-hidden shadow-inner">
        {data.map((value, i) => {
          const intensity = normalize(value);
          const red = Math.floor(255 * intensity);
          const blue = Math.floor(255 * (1 - intensity));

          return (
            <div
              key={i}
              className="w-full h-full"
              style={{
                backgroundColor: `rgb(${red},0,${blue})`
              }}
            />
          );
        })}
      </div>

      {/* Fixed Scale Legend */}
      <div className="flex flex-col items-center h-64 justify-between">

        {/* Max */}
        <span className="text-sm text-gray-300">
          {MAX_TEMP}°C
        </span>

        {/* Gradient */}
        <div
          className="w-6 flex-1 my-2 rounded-md"
          style={{
            background: "linear-gradient(to top, blue, cyan, yellow, red)"
          }}
        />

        {/* Min */}
        <span className="text-sm text-gray-300">
          {MIN_TEMP}°C
        </span>

      </div>
    </div>
  );
}


/* ================= CONFIDENCE BAR ================= */

function ConfidenceBar({ value }) {
  const percentage = Math.min(Math.max(value * 100, 0), 100);

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span>Confidence</span>
        <span>{percentage.toFixed(1)}%</span>
      </div>

      <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 via-yellow-400 to-red-500 transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

/* ================= MAIN APP ================= */

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

  const fireActive = vision?.detected;
  const alertActive = alert && alert.status !== "NO_ALERT";

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <h1 className="text-3xl font-bold mb-10">
        🔥 AI Fire and Smoke Surveillance System
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* LIVE CAMERA */}
        <Card
          title="Live Camera"
          className="lg:col-span-2 lg:row-span-2"
        >
          <img
            src={`${API}/vision/video_feed`}
            alt="Live Feed"
            className="rounded-xl w-full border border-gray-700"
          />
        </Card>

        {/* THERMAL WITH LEGEND */}
        <Card title="Thermal Camera (8x8)">
          {sensor?.thermal ? (
            <ThermalGrid data={sensor.thermal} />
          ) : (
            <p>No thermal data</p>
          )}
        </Card>

        {/* VISION WITH CONFIDENCE BAR */}
        <Card
          title="Vision AI"
          className={
            fireActive
              ? "border-2 border-red-500 shadow-red-500/30"
              : ""
          }
        >
          {vision ? (
            <div className="space-y-4">

              <p className="text-lg">
                Fire Detected:{" "}
                <span className={fireActive ? "text-red-400 font-bold" : ""}>
                  {fireActive ? "🔥 YES" : "No"}
                </span>
              </p>

              <ConfidenceBar value={vision.confidence || 0} />

              <p>
                Updated:{" "}
                <Freshness timestamp={vision.timestamp} />
              </p>

            </div>
          ) : (
            <p>No vision data</p>
          )}
        </Card>

        {/* CURRENT ALERT */}
        <Card
          title="Current Alert"
          className={
            alertActive
              ? "border-2 border-red-600 animate-pulse"
              : ""
          }
        >
          {alertActive ? (
            <div className="space-y-3">
              <p>Status: {alert.status}</p>
              <p>Type: {alert.type}</p>
              <p>Source: {alert.source}</p>
              <p>Confidence: {alert.confidence}</p>
              <p>
                Updated:{" "}
                <Freshness timestamp={alert.updated_at} />
              </p>
            </div>
          ) : (
            <p>No active alert</p>
          )}
        </Card>

        {/* ALERT HISTORY */}
        <Card title="Alert History">
          {history.length > 0 ? (
            <ul className="space-y-2 text-sm">
              {history.slice(0, 5).map((a, i) => (
                <li
                  key={i}
                  className="border-b border-gray-700 pb-2"
                >
                  {a.type} | {a.status}
                </li>
              ))}
            </ul>
          ) : (
            <p>No alerts yet</p>
          )}
        </Card>

        {/* SENSORS */}
        <Card title="Sensors">
          {sensor ? (
            <div className="space-y-3">
              <p>
                Flame: {sensor.flame ? "🔥 DETECTED" : "No flame"}
              </p>
              <p>MQ135: {sensor.mq135_raw}</p>
              <p>
                Thermal Max:{" "}
                {sensor.thermal
                  ? Math.max(...sensor.thermal).toFixed(2)
                  : "N/A"}
              </p>
              <p>
                Updated:{" "}
                <Freshness timestamp={sensor.timestamp} />
              </p>
            </div>
          ) : (
            <p>No sensor data</p>
          )}
        </Card>

      </div>
    </div>
  );
}
