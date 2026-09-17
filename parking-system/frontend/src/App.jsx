import { useEffect, useState, useCallback } from "react";
import { Routes, Route, useLocation, Navigate } from "react-router-dom";
import { api } from "./api";
import SearchPanel from "./components/SearchPanel";
import CheckInModal from "./components/CheckInModal";
import OccupiedModal from "./components/OccupiedModal";
import Home from "./pages/Home";
import ParkingView from "./pages/ParkingView";
import Landing from "./pages/Landing";
import LoginPage from "./pages/LoginPage";
import ReportsPage from "./pages/ReportsPage";

const ROLE_ACCESS = {
  Admin: ["/dashboard", "/parking/*"],
  Attendant: ["/dashboard", "/parking/*"],
  "Security / Manager": ["/dashboard"],
};

export default function App() {
  const [slots, setSlots] = useState([]);
  const [dashboard, setDashboard] = useState({ categories: [] });
  const [checkInSlot, setCheckInSlot] = useState(null);
  const [checkInOpen, setCheckInOpen] = useState(false);
  const [occupiedSlot, setOccupiedSlot] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem("parking-user") || "null"));
  const location = useLocation();

  const refresh = useCallback(async () => {
    try {
      const [slotList, dash] = await Promise.all([api.getSlots(), api.getDashboard()]);
      setSlots(slotList);
      setDashboard(dash);
      setLoadError("");
    } catch (e) {
      setLoadError("Could not reach the backend. Is it running on port 8000?");
    }
  }, []);

  useEffect(() => {
    refresh();
    let ws;
    try {
      ws = new WebSocket(api.wsUrl());
      ws.onmessage = () => refresh();
    } catch {
      // dashboard still works via manual actions
    }
    return () => ws && ws.close();
  }, [refresh]);

  const handleSlotClick = (slot) => {
    if (slot.is_occupied) {
      setOccupiedSlot(slot);
    } else {
      setCheckInSlot(slot);
      setCheckInOpen(true);
    }
  };

  const handleCheckIn = async (plate, vehicleType, slotId) => {
    await api.checkIn(plate, vehicleType, slotId);
    await refresh();
  };

  useEffect(() => {
    if (user) {
      localStorage.setItem("parking-user", JSON.stringify(user));
    } else {
      localStorage.removeItem("parking-user");
    }
  }, [user]);

  const isLandingPage = location.pathname === "/";

  const requireAuth = (element, allowedRoles) => {
    if (!user) {
      return <Navigate to="/login" replace />;
    }
    if (!allowedRoles.includes(user.role)) {
      return <Navigate to="/dashboard" replace />;
    }
    return element;
  };

  const handleLogout = () => {
    setUser(null);
  };

  return (
    <div className={isLandingPage ? "" : "app"}>
      {!isLandingPage && user && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", marginBottom: "18px", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontWeight: 600 }}>{user.name}</div>
            <div style={{ fontSize: "13px", color: "#7a7870" }}>{user.role}</div>
          </div>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <button onClick={() => window.location.href = "/dashboard"}>Dashboard</button>
            {(user.role === "Admin" || user.role === "Security / Manager") && (
              <button onClick={() => window.location.href = "/reports"}>Reports</button>
            )}
            <button onClick={handleLogout}>Logout</button>
          </div>
        </div>
      )}

      {!isLandingPage && !user && <Navigate to="/login" replace />}
      {!isLandingPage && loadError && <p className="error">{loadError}</p>}
      {!isLandingPage && user && <SearchPanel onChanged={refresh} />}

      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage onLogin={setUser} />} />
        <Route
          path="/dashboard"
          element={requireAuth(
            <Home dashboard={dashboard} refresh={refresh} setCheckInOpen={setCheckInOpen} user={user} />,
            ["Admin", "Attendant", "Security / Manager"]
          )}
        />
        <Route
          path="/parking/:type"
          element={requireAuth(
            <ParkingView slots={slots} onSlotClick={handleSlotClick} setCheckInOpen={setCheckInOpen} />,
            ["Admin", "Attendant"]
          )}
        />
        <Route
          path="/reports"
          element={requireAuth(<ReportsPage />, ["Admin", "Security / Manager"])}
        />
      </Routes>

      {user && checkInOpen && (
        <CheckInModal
          defaultType={checkInSlot?.type || "compact"}
          slot={checkInSlot}
          onClose={() => { setCheckInOpen(false); setCheckInSlot(null); }}
          onSubmit={handleCheckIn}
        />
      )}

      {user && occupiedSlot && (
        <OccupiedModal
          slot={occupiedSlot}
          onClose={() => setOccupiedSlot(null)}
          onChanged={refresh}
        />
      )}
    </div>
  );
}
