import { useEffect, useState } from "react";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function ReportsPage() {
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    loadReport(date);
  }, [date]);

  const loadReport = async (selectedDate) => {
    try {
      const res = await fetch(`${BASE_URL}/daily-report?date=${selectedDate}`);
      if (!res.ok) {
        throw new Error("No report available for this date.");
      }
      const data = await res.json();
      setReport(data);
      setError("");
    } catch (e) {
      setReport(null);
      setError(e.message || "Unable to load report.");
    }
  };

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", paddingBottom: "40px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "16px", marginBottom: "24px", flexWrap: "wrap" }}>
        <div>
          <h1 style={{ margin: 0 }}>Daily Reports</h1>
          <p style={{ margin: "8px 0 0", color: "#7a7870" }}>View profit, cars processed, and per-vehicle charges.</p>
        </div>
        <label style={{ display: "flex", flexDirection: "column", fontSize: "13px", color: "#7a7870", gap: "6px" }}>
          Select date
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            style={{ height: "40px", border: "1px solid #d9d4ca", borderRadius: "10px", padding: "0 10px" }}
          />
        </label>
      </div>

      {error && <p className="error">{error}</p>}

      {report && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "16px", marginBottom: "24px" }}>
            <div className="stat-card">
              <div className="label">Cars processed</div>
              <div className="value">{report.total_cars}</div>
            </div>
            <div className="stat-card">
              <div className="label">Total profit</div>
              <div className="value">₹{Number(report.total_profit || 0).toFixed(2)}</div>
            </div>
            <div className="stat-card">
              <div className="label">Vehicle mix</div>
              <div className="value">{Object.values(report.cars_by_type || {}).reduce((sum, val) => sum + val, 0)}</div>
            </div>
          </div>

          <div className="panel">
            <h2>Vehicle types</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px" }}>
              {Object.entries(report.cars_by_type || {}).map(([type, count]) => (
                <div key={type} style={{ background: "#f8f7f3", border: "1px solid #e2e0d8", borderRadius: "10px", padding: "14px" }}>
                  <div style={{ fontSize: "12px", color: "#7a7870", textTransform: "capitalize" }}>{type}</div>
                  <div style={{ fontSize: "1.8rem", fontWeight: 600 }}>{count}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel" style={{ marginTop: "24px" }}>
            <h2>Per-car revenue</h2>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                <thead>
                  <tr style={{ background: "#f8f7f3" }}>
                    <th style={{ textAlign: "left", padding: "10px 12px", borderBottom: "1px solid #e2e0d8" }}>Plate</th>
                    <th style={{ textAlign: "left", padding: "10px 12px", borderBottom: "1px solid #e2e0d8" }}>Type</th>
                    <th style={{ textAlign: "left", padding: "10px 12px", borderBottom: "1px solid #e2e0d8" }}>Entry</th>
                    <th style={{ textAlign: "left", padding: "10px 12px", borderBottom: "1px solid #e2e0d8" }}>Exit</th>
                    <th style={{ textAlign: "left", padding: "10px 12px", borderBottom: "1px solid #e2e0d8" }}>Charged</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.values(report.per_car || {}).map((entry) => (
                    <tr key={entry.plate}>
                      <td style={{ padding: "10px 12px", borderBottom: "1px solid #efeae0" }}>{entry.plate}</td>
                      <td style={{ padding: "10px 12px", borderBottom: "1px solid #efeae0" }}>{entry.vehicle_type}</td>
                      <td style={{ padding: "10px 12px", borderBottom: "1px solid #efeae0" }}>{new Date(entry.entry_time).toLocaleString()}</td>
                      <td style={{ padding: "10px 12px", borderBottom: "1px solid #efeae0" }}>{entry.exit_time ? new Date(entry.exit_time).toLocaleString() : "—"}</td>
                      <td style={{ padding: "10px 12px", borderBottom: "1px solid #efeae0" }}>₹{Number(entry.amount_charged || 0).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
