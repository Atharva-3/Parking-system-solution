import { useEffect, useState, useCallback } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import { api } from "./api";
import SearchPanel from "./components/SearchPanel";
import CheckInModal from "./components/CheckInModal";
import OccupiedModal from "./components/OccupiedModal";
import Home from "./pages/Home";
import ParkingView from "./pages/ParkingView";
import Landing from "./pages/Landing";

export default function App() {
  const [slots, setSlots] = useState([]);
  const [dashboard, setDashboard] = useState({ categories: [] });
  const [checkInSlot, setCheckInSlot] = useState(null);
  const [checkInOpen, setCheckInOpen] = useState(false);
  const [occupiedSlot, setOccupiedSlot] = useState(null);
  const [loadError, setLoadError] = useState("");
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

  const isLandingPage = location.pathname === "/";

  return (
    <div className={isLandingPage ? "" : "app"}>
      {!isLandingPage && <h1>Parking garage dashboard</h1>}
      {!isLandingPage && loadError && <p className="error">{loadError}</p>}
      {!isLandingPage && <SearchPanel onChanged={refresh} />}

      <Routes>
        <Route path="/" element={<Landing />} />
        <Route 
          path="/dashboard" 
          element={
            <Home 
              dashboard={dashboard} 
              refresh={refresh} 
              setCheckInOpen={setCheckInOpen} 
            />
          } 
        />
        <Route 
          path="/parking/:type" 
          element={
            <ParkingView 
              slots={slots} 
              onSlotClick={handleSlotClick} 
              setCheckInOpen={setCheckInOpen} 
            />
          } 
        />
      </Routes>

      {checkInOpen && (
        <CheckInModal
          defaultType={checkInSlot?.type || "compact"}
          slot={checkInSlot}
          onClose={() => { setCheckInOpen(false); setCheckInSlot(null); }}
          onSubmit={handleCheckIn}
        />
      )}

      {occupiedSlot && (
        <OccupiedModal
          slot={occupiedSlot}
          onClose={() => setOccupiedSlot(null)}
          onChanged={refresh}
        />
      )}
    </div>
  );
}
