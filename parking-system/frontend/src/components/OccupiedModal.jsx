import { useState } from "react";
import { api } from "../api";

export default function OccupiedModal({ slot, onClose, onChanged }) {
  const ticket = slot.active_ticket;
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const checkout = async () => {
    if (!ticket) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.checkOut(ticket.plate);
      onChanged();
      onClose();
      alert(
        `Checked out ${result.ticket.plate} from ${result.ticket.slot_code}. ` +
        `${result.hours_charged}h charged, amount: ₹${result.amount}`
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const sensorExit = async () => {
    setBusy(true);
    setError("");
    try {
      const result = await api.simulateSensor(slot.id, false);
      onChanged();
      onClose();
      alert(
        `Sensor vacated ${slot.code}. ${result.ticket.plate}: ` +
        `${result.hours_charged}h, ₹${result.amount}`
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>{slot.code} — occupied</h3>
        {ticket ? (
          <div className="result-card" style={{ marginTop: 0 }}>
            <strong>{ticket.plate}</strong> ({ticket.vehicle_type})<br />
            Checked in: {new Date(ticket.entry_time).toLocaleString()}
          </div>
        ) : (
          <p className="hint">Occupied, but no ticket is attached to this slot.</p>
        )}
        {error && <p className="error" style={{ marginTop: 10 }}>{error}</p>}
        <div className="modal-actions">
          <button onClick={onClose}>Close</button>
          <button onClick={sensorExit} disabled={busy || !ticket}>Sensor exit</button>
          <button className="primary" onClick={checkout} disabled={busy || !ticket}>
            {busy ? "Processing…" : "Check out"}
          </button>
        </div>
      </div>
    </div>
  );
}
