import { useEffect, useState } from "react";

function App() {
  const [health, setHealth] = useState("loading...");
  useEffect(() => {
    const api = import.meta.env.VITE_API_URL || "http://localhost:8000";
    fetch(`${api}/api/healthz`)
      .then(r => r.json())
      .then(d => setHealth(JSON.stringify(d)))
      .catch(() => setHealth("api unreachable"));
  }, []);
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="p-6 rounded-xl border">
        <h1 className="text-2xl font-bold mb-2">AI Influencer Studio</h1>
        <p>Backend health: {health}</p>
      </div>
    </div>
  );
}
export default App;
