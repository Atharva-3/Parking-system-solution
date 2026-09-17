import { useState } from "react";

const LABELS = { compact: "Compact", standard: "Standard", ev: "EV" };

/** Vehicle types allowed on a given slot type (same overflow rules as the backend). */
export function typesAllowedOnSlot(slotType) {
  if (slotType === "compact") return ["compact"];
  if (slotType === "standard") return ["compact", "standard"];
  if (slotType === "ev") return ["ev"];
  return ["compact", "standard", "ev"];
}

export default function CheckInModal({ defaultType, slot, onClose, onSubmit }) {
  const allowed = slot ? typesAllowedOnSlot(slot.type) : ["compact", "standard", "ev"];
  const [plate, setPlate] = useState("");
  const [vehicleType, setVehicleType] = useState(
    allowed.includes(defaultType) ? defaultType : allowed[0]
  );
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!plate.trim()) {
      setError("Enter a plate number first.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await onSubmit(plate, vehicleType, slot?.id);
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>{slot ? `Check in to ${slot.code}` : "Check in a vehicle"}</h3>
        {slot && (
          <p className="hint">
            This tile is a {LABELS[slot.type]} slot. The car will be assigned here, not auto-picked.
          </p>
        )}
        <label htmlFor="plate">Plate number</label>
        <input id="plate" placeholder="RJ14 AB 1234" value={plate} onChange={(e) => setPlate(e.target.value)} />
        {allowed.length > 1 && (
          <>
            <label htmlFor="vtype">Vehicle type</label>
            <select id="vtype" value={vehicleType} onChange={(e) => setVehicleType(e.target.value)}>
              {allowed.map((t) => (
                <option key={t} value={t}>{LABELS[t]}</option>
              ))}
            </select>
          </>
        )}
        {error && <p className="error" style={{ marginTop: 10 }}>{error}</p>}
        <div className="modal-actions">
          <button onClick={onClose}>Cancel</button>
          <button className="primary" onClick={handleSubmit} disabled={submitting}>
            {submitting ? "Checking in…" : "Check in"}
          </button>
        </div>
      </div>
    </div>
  );
}
