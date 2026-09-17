import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import StatsBar from "../components/StatsBar";
import HardwareSim from "../components/HardwareSim";
import PricingPanel from "../components/PricingPanel";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Home({ dashboard, refresh, setCheckInOpen, user }) {
  const totalVacantSpaces = dashboard.categories?.reduce((acc, cat) => acc + cat.free, 0) || 0;
  const isAdmin = user?.role === "Admin";
  const isAttendant = user?.role === "Attendant";
  const isManager = user?.role === "Security / Manager";
  const [dailyReport, setDailyReport] = useState(null);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const today = new Date().toISOString().slice(0, 10);
    fetch(`${BASE_URL}/daily-report?date=${today}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setDailyReport(data))
      .catch(() => setDailyReport(null));

    fetch(`${BASE_URL}/alerts`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setAlerts(data))
      .catch(() => setAlerts([]));
  }, []);

  return (
    <div className="home-page">
      <div className="overall-stats" style={{ display: 'flex', gap: '20px', marginBottom: '20px', marginTop: '20px' }}>
        <div className="stat-card" style={{ padding: '20px', background: 'var(--surface-overlay)', borderRadius: '8px', flex: 1, border: '1px solid var(--border)' }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '1rem', color: 'var(--text-muted)' }}>Total cars present</h3>
          <p style={{ fontSize: '2rem', fontWeight: 'bold', margin: 0 }}>{dashboard.total_active_tickets || 0}</p>
        </div>
        <div className="stat-card" style={{ padding: '20px', background: 'var(--surface-overlay)', borderRadius: '8px', flex: 1, border: '1px solid var(--border)' }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '1rem', color: 'var(--text-muted)' }}>Total vacant spaces</h3>
          <p style={{ fontSize: '2rem', fontWeight: 'bold', margin: 0 }}>{totalVacantSpaces}</p>
        </div>
        <div className="stat-card" style={{ padding: '20px', background: 'var(--surface-overlay)', borderRadius: '8px', flex: 1, border: '1px solid var(--border)' }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '1rem', color: 'var(--text-muted)' }}>Profit earned</h3>
          <p style={{ fontSize: '2rem', fontWeight: 'bold', margin: 0, color: 'var(--brand)' }}>₹{dashboard.profit_earned?.toFixed(2) || "0.00"}</p>
        </div>
      </div>

      <div style={{ height: 10 }} />
      <StatsBar categories={dashboard.categories || []} />

      {(isAdmin || isAttendant) && (
        <div className="toolbar" style={{ justifyContent: "space-between", margin: "30px 0 15px 0" }}>
          <h3 style={{ margin: 0 }}>Parking Areas</h3>
          <button className="primary" onClick={() => setCheckInOpen(true)}>
            + Check in a vehicle
          </button>
        </div>
      )}

      {(isAdmin || isAttendant) && (
        <div className="parking-links" style={{ display: 'flex', gap: '20px', marginBottom: '40px' }}>
          <Link to="/parking/compact" style={{ textDecoration: 'none', flex: 1 }}>
            <div className="parking-card" style={{ padding: '30px', background: 'var(--surface-overlay)', border: '1px solid var(--border)', borderRadius: '8px', textAlign: 'center', cursor: 'pointer', fontSize: '1.2em', fontWeight: 'bold', transition: 'all 0.2s' }}>
              Compact
            </div>
          </Link>
          <Link to="/parking/standard" style={{ textDecoration: 'none', flex: 1 }}>
            <div className="parking-card" style={{ padding: '30px', background: 'var(--surface-overlay)', border: '1px solid var(--border)', borderRadius: '8px', textAlign: 'center', cursor: 'pointer', fontSize: '1.2em', fontWeight: 'bold', transition: 'all 0.2s' }}>
              Standard
            </div>
          </Link>
          <Link to="/parking/ev" style={{ textDecoration: 'none', flex: 1 }}>
            <div className="parking-card" style={{ padding: '30px', background: 'var(--surface-overlay)', border: '1px solid var(--border)', borderRadius: '8px', textAlign: 'center', cursor: 'pointer', fontSize: '1.2em', fontWeight: 'bold', transition: 'all 0.2s' }}>
              EV
            </div>
          </Link>
        </div>
      )}

      {(isAdmin || isManager) && dailyReport && (
        <div className="panel">
          <h2>Daily Profit Report</h2>
          <p className="hint">Summary for {dailyReport.date}</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '12px', marginTop: '12px' }}>
            <div className="stat-card">
              <div className="label">Cars</div>
              <div className="value">{dailyReport.total_cars}</div>
            </div>
            <div className="stat-card">
              <div className="label">Profit</div>
              <div className="value">₹{Number(dailyReport.total_profit || 0).toFixed(2)}</div>
            </div>
            <div className="stat-card">
              <div className="label">Types</div>
              <div className="value">{Object.values(dailyReport.cars_by_type || {}).reduce((a, b) => a + b, 0)}</div>
            </div>
          </div>
        </div>
      )}

      {isAdmin && <PricingPanel />}

      {(isManager || isAdmin) && (
        <div className="panel">
          <h2>Security / Manager Overview</h2>
          <p className="hint">Monitor active sessions, overdue entries, and system alerts in one place.</p>
          {alerts.length === 0 ? (
            <p className="ok">No active alerts.</p>
          ) : (
            <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.8, color: "var(--text-muted)" }}>
              {alerts.map((alert, idx) => (
                <li key={`${alert.type}-${alert.plate || idx}`}>
                  {alert.type === "overdue" ? `${alert.plate} has been parked for ${alert.hours_parked} hours.` : `${alert.plate} has duplicate active records.`}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {(isAdmin || isAttendant) && <HardwareSim onChanged={refresh} />}
    </div>
  );
}
