import { Link } from "react-router-dom";
import StatsBar from "../components/StatsBar";
import HardwareSim from "../components/HardwareSim";
import PricingPanel from "../components/PricingPanel";

export default function Home({ dashboard, refresh, setCheckInOpen }) {
  const totalVacantSpaces = dashboard.categories?.reduce((acc, cat) => acc + cat.free, 0) || 0;

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

      <div className="toolbar" style={{ justifyContent: "space-between", margin: "30px 0 15px 0" }}>
        <h3 style={{ margin: 0 }}>Parking Areas</h3>
        <button className="primary" onClick={() => setCheckInOpen(true)}>
          + Check in a vehicle
        </button>
      </div>

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

      <HardwareSim onChanged={refresh} />
      <PricingPanel />
    </div>
  );
}
