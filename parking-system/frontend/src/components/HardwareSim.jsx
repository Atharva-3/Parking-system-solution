import { useState } from "react";
import { api } from "../api";

export default function HardwareSim({ onChanged }) {
  const [vehicleType, setVehicleType] = useState("compact");
  const [plate, setPlate] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleAnpr = async () => {
    setBusy(true);
    setError("");
    try {
      const ticket = await api.simulateAnpr(vehicleType, plate.trim() || undefined);
      onChanged();
      setPlate("");
      alert(`ANPR checked in ${ticket.plate} → ${ticket.slot_code}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="panel">
      <h2>Camera simulation (ANPR)</h2>
      <p className="hint">
        A real camera would OCR the plate and POST it here. Leave plate blank to invent an OCR result.
        Slot sensors are simulated from an occupied tile (“Sensor exit”).
      </p>
      <div className="toolbar" style={{ marginBottom: 0 }}>
        <input
          placeholder="Optional plate (blank = fake OCR)"
          value={plate}
          onChange={(e) => setPlate(e.target.value)}
        />
        <select value={vehicleType} onChange={(e) => setVehicleType(e.target.value)}>
          <option value="compact">Compact</option>
          <option value="standard">Standard</option>
          <option value="ev">EV</option>
        </select>
        <button className="primary" onClick={handleAnpr} disabled={busy}>
          Simulate camera
        </button>
      </div>
      {error && <p className="error" style={{ margin: "10px 0 0" }}>{error}</p>}
    </div>
  );
}
