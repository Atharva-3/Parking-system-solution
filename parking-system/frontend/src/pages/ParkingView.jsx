import { Link, useParams } from "react-router-dom";
import SlotSection from "../components/SlotSection";

export default function ParkingView({ slots, onSlotClick, setCheckInOpen }) {
  const { type } = useParams();

  // Make sure type is valid, fallback to compact if not
  const validTypes = ["compact", "standard", "ev"];
  const currentType = validTypes.includes(type) ? type : "compact";
  
  const filteredSlots = slots.filter((s) => s.type === currentType);

  return (
    <div className="parking-view">
      <div className="toolbar" style={{ justifyContent: "space-between", margin: "20px 0" }}>
        <Link to="/dashboard" style={{ textDecoration: 'none' }}>
          <button className="secondary">← Back to Dashboard</button>
        </Link>
        <button className="primary" onClick={() => setCheckInOpen(true)}>
          + Check in a vehicle
        </button>
      </div>

      <SlotSection
        type={currentType}
        slots={filteredSlots}
        onSlotClick={onSlotClick}
      />
      
      <div className="legend" style={{ marginTop: '20px' }}>
        <span><span className="swatch" style={{ background: "var(--free)" }} />Free — click to park in that slot</span>
        <span><span className="swatch" style={{ background: "var(--occupied)" }} />Occupied — click for car details</span>
      </div>
    </div>
  );
}
