import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div style={{ fontFamily: 'Inter, sans-serif', color: 'var(--text)', paddingBottom: '50px' }}>
      
      {/* Hero Section */}
      <section style={{ textAlign: 'center', padding: '80px 20px', background: 'linear-gradient(135deg, var(--surface-overlay) 0%, var(--background) 100%)', borderBottom: '1px solid var(--border)' }}>
        <h1 style={{ fontSize: '3rem', margin: '0 0 20px 0', color: 'var(--brand)' }}>Next-Gen Parking System</h1>
        <p style={{ fontSize: '1.2rem', maxWidth: '600px', margin: '0 auto 40px auto', color: 'var(--text-muted)' }}>
          A real-time, end-to-end parking allocation and automated billing system designed to maximize efficiency and revenue for modern garages.
        </p>
        <Link to="/dashboard">
          <button className="primary" style={{ fontSize: '1.2rem', padding: '15px 30px', cursor: 'pointer' }}>
            Go to Dashboard
          </button>
        </Link>
      </section>

      {/* Key Features */}
      <section style={{ padding: '60px 20px', maxWidth: '1000px', margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '40px', fontSize: '2rem' }}>Key Features</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
          
          <div style={{ padding: '30px', background: 'var(--surface-overlay)', borderRadius: '8px', border: '1px solid var(--border)' }}>
            <h3>📡 Live Allocation</h3>
            <p style={{ color: 'var(--text-muted)' }}>Real-time updates across all dashboards using WebSockets. See what's occupied instantly.</p>
          </div>
          
          <div style={{ padding: '30px', background: 'var(--surface-overlay)', borderRadius: '8px', border: '1px solid var(--border)' }}>
            <h3>🔄 Smart Overflow</h3>
            <p style={{ color: 'var(--text-muted)' }}>Automatically route Compact cars to Standard slots when full to maximize capacity.</p>
          </div>
          
          <div style={{ padding: '30px', background: 'var(--surface-overlay)', borderRadius: '8px', border: '1px solid var(--border)' }}>
            <h3>⚡ EV Tracking</h3>
            <p style={{ color: 'var(--text-muted)' }}>Dedicated tracking for EV charging stations, ensuring only EVs park in specialized spots.</p>
          </div>
          
          <div style={{ padding: '30px', background: 'var(--surface-overlay)', borderRadius: '8px', border: '1px solid var(--border)' }}>
            <h3>💳 Automated Billing</h3>
            <p style={{ color: 'var(--text-muted)' }}>Dynamic pricing rules stored in the database compute complex tier-based parking fees automatically.</p>
          </div>
          
        </div>
      </section>

      {/* Target Audience & How it Helps */}
      <section style={{ padding: '60px 20px', background: 'var(--surface-overlay)', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexWrap: 'wrap', gap: '40px' }}>
          
          <div style={{ flex: '1 1 400px' }}>
            <h2 style={{ fontSize: '2rem' }}>Target Audience</h2>
            <ul style={{ lineHeight: '1.8', color: 'var(--text-muted)', fontSize: '1.1rem' }}>
              <li><strong>Commercial Garage Operators:</strong> Looking to modernize their tracking and billing.</li>
              <li><strong>Mall Management:</strong> Needing real-time capacity overview for different vehicle types.</li>
              <li><strong>Smart City Planners:</strong> Integrating EV infrastructure into urban parking planning.</li>
            </ul>
          </div>
          
          <div style={{ flex: '1 1 400px' }}>
            <h2 style={{ fontSize: '2rem' }}>How it Helps</h2>
            <p style={{ lineHeight: '1.8', color: 'var(--text-muted)', fontSize: '1.1rem' }}>
              By moving away from manual paper tickets and static maps, our system <strong>maximizes occupancy rates</strong> and ensures accurate billing. It eliminates human error in fee calculation and provides a bird's-eye view of your entire operation, reducing operational overhead and increasing customer satisfaction.
            </p>
          </div>

        </div>
      </section>

      {/* Future Roadmap */}
      <section style={{ padding: '60px 20px', maxWidth: '1000px', margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '40px', fontSize: '2rem' }}>Future Roadmap</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          <div style={{ padding: '20px', borderLeft: '4px solid var(--brand)', background: 'var(--surface-overlay)', borderRadius: '0 8px 8px 0' }}>
            <h3 style={{ margin: '0 0 10px 0' }}>1. User Authentication & Roles</h3>
            <p style={{ margin: 0, color: 'var(--text-muted)' }}>Implement secure logins with Admin (can change pricing) and Attendant (can check-in/out) roles.</p>
          </div>
          
          <div style={{ padding: '20px', borderLeft: '4px solid var(--brand)', background: 'var(--surface-overlay)', borderRadius: '0 8px 8px 0' }}>
            <h3 style={{ margin: '0 0 10px 0' }}>2. Advanced Analytics & Reporting</h3>
            <p style={{ margin: 0, color: 'var(--text-muted)' }}>Historical trend charts, peak hour heatmaps, and automated daily revenue email summaries.</p>
          </div>
          
          <div style={{ padding: '20px', borderLeft: '4px solid var(--brand)', background: 'var(--surface-overlay)', borderRadius: '0 8px 8px 0' }}>
            <h3 style={{ margin: '0 0 10px 0' }}>3. Customer Mobile App & Pre-booking</h3>
            <p style={{ margin: 0, color: 'var(--text-muted)' }}>Allow customers to reserve spots in advance, pay via their phones, and navigate directly to their assigned slot.</p>
          </div>

        </div>
      </section>
      
    </div>
  );
}
