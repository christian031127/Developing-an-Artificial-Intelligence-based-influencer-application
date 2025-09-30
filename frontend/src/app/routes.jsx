import { useEffect, useState } from "react";
import Layout from "./layout";
import Dashboard from "../pages/Dashboard";
import Analytics from "../pages/Analytics";
import Characters from "../pages/Characters";
import { api } from "../lib/api";

export default function AppRoutes() {
  const [health, setHealth] = useState("checking...");
  const [page, setPage] = useState("dashboard"); // "dashboard" | "analytics"

  useEffect(() => {
    api.health().then((d) => setHealth(JSON.stringify(d))).catch(() => setHealth("api unreachable"));
  }, []);

  return (
    <Layout page={page} onNavigate={setPage}>
      {page === "dashboard" && <Dashboard health={health} />}
      {page === "analytics" && <Analytics />}
      {page === "characters" && <Characters />}
    </Layout>
  );
}
