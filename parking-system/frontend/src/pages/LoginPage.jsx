import { useState } from "react";

const DEMO_USERS = {
  admin: { password: "admin123", role: "Admin", name: "System Admin" },
  attendant: { password: "attendant123", role: "Attendant", name: "Garage Attendant" },
  viewer: { password: "viewer123", role: "Security / Manager", name: "Security Manager" },
};

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const user = DEMO_USERS[username.toLowerCase()];
    if (!user || user.password !== password) {
      setError("Invalid username or password.");
      return;
    }
    onLogin({
      username: username.toLowerCase(),
      role: user.role,
      name: user.name,
    });
  };

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "linear-gradient(135deg, #f5f4f0 0%, #edf5ff 100%)" }}>
      <div style={{ width: "100%", maxWidth: "520px", background: "white", border: "1px solid #e2e0d8", borderRadius: "18px", padding: "32px 28px", boxShadow: "0 18px 40px rgba(24, 95, 165, 0.08)" }}>
        <h1 style={{ marginBottom: "8px", fontSize: "2rem", textAlign: "center" }}>Parking Control</h1>
        <p style={{ margin: "0 0 24px", textAlign: "center", color: "#7a7870" }}>Select a role and sign in to continue</p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "12px", marginBottom: "20px" }}>
          {Object.entries(DEMO_USERS).map(([key, user]) => (
            <button
              key={key}
              type="button"
              className={username === key ? "primary" : ""}
              onClick={() => {
                setUsername(key);
                setPassword({ admin: "admin123", attendant: "attendant123", viewer: "viewer123" }[key]);
                setError("");
              }}
              style={{
                height: "auto",
                padding: "12px 8px",
                fontWeight: "600",
                borderRadius: "10px",
                textAlign: "center",
              }}
            >
              {user.role}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          <label style={{ display: "block", marginBottom: "8px", fontWeight: "600" }}>Username</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="admin"
            style={{ width: "100%", height: "42px", borderRadius: "10px", border: "1px solid #d9d4ca", padding: "0 12px", marginBottom: "16px" }}
          />

          <label style={{ display: "block", marginBottom: "8px", fontWeight: "600" }}>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            style={{ width: "100%", height: "42px", borderRadius: "10px", border: "1px solid #d9d4ca", padding: "0 12px", marginBottom: "16px" }}
          />

          {error && <p style={{ color: "#a32d2d", margin: "0 0 14px" }}>{error}</p>}

          <button type="submit" className="primary" style={{ width: "100%", height: "44px", fontSize: "1rem" }}>
            Login
          </button>
        </form>

        <div style={{ marginTop: "18px", color: "#7a7870", fontSize: "0.9rem", lineHeight: "1.6" }}>
          <strong>Demo accounts:</strong><br />
          Admin: admin / admin123<br />
          Attendant: attendant / attendant123<br />
          Security: viewer / viewer123
        </div>
      </div>
    </div>
  );
}
