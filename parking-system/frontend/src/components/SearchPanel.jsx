import { useState } from "react";
import { api } from "../api";

export default function SearchPanel({ onChanged }) {
  const [plate, setPlate] = useState("");
  const [ticket, setTicket] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSearch = async () => {
    if (!plate.trim()) {
      setError("Enter a plate to search.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      const result = await api.search(plate);
      setTicket(result);
    } catch (e) {
      setTicket(null);
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const handleCheckout = async () => {
    setBusy(true);
    setError("");
    try {
      const result = await api.checkOut(ticket.plate);
      setTicket(null);
      onChanged();
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

  return (
    <div>
      <div className="toolbar">
        <input
          placeholder="Search by plate, e.g. RJ14 AB 1234"
          value={plate}
          onChange={(e) => setPlate(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <button onClick={handleSearch} disabled={busy}>Search</button>
      </div>
      {error && <p className="error">{error}</p>}
      {ticket && (
        <div className="result-card">
          <strong>{ticket.plate}</strong> — slot {ticket.slot_code} ({ticket.vehicle_type})<br />
          Checked in: {new Date(ticket.entry_time).toLocaleString()}
          <div className="modal-actions" style={{ marginTop: 12, justifyContent: "flex-start" }}>
            <button className="primary" onClick={handleCheckout} disabled={busy}>
              {busy ? "Processing…" : "Check out"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
