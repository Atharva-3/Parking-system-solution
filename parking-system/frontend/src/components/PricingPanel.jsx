import { useEffect, useState } from "react";
import { api } from "../api";

export default function PricingPanel({ onSaved }) {
  const [form, setForm] = useState(null);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getPricing()
      .then(setForm)
      .catch((e) => setError(e.message));
  }, []);

  const setField = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSaved("");
  };

  const save = async () => {
    setBusy(true);
    setError("");
    try {
      const next = await api.updatePricing({
        first_hour_rate: Number(form.first_hour_rate),
        additional_hour_rate: Number(form.additional_hour_rate),
        daily_cap: Number(form.daily_cap),
      });
      setForm(next);
      setSaved("Rates saved. New check-outs will use these.");
      onSaved?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  if (!form) {
    return error ? <p className="error">{error}</p> : null;
  }

  return (
    <div className="panel">
      <h2>Pricing</h2>
      <p className="hint">Stored in the database — change without a code deploy.</p>
      <div className="pricing-grid">
        <label>
          First hour (₹)
          <input
            type="number"
            min="0"
            value={form.first_hour_rate}
            onChange={(e) => setField("first_hour_rate", e.target.value)}
          />
        </label>
        <label>
          Extra hour (₹)
          <input
            type="number"
            min="0"
            value={form.additional_hour_rate}
            onChange={(e) => setField("additional_hour_rate", e.target.value)}
          />
        </label>
        <label>
          Daily cap (₹)
          <input
            type="number"
            min="0"
            value={form.daily_cap}
            onChange={(e) => setField("daily_cap", e.target.value)}
          />
        </label>
      </div>
      {error && <p className="error">{error}</p>}
      {saved && <p className="ok">{saved}</p>}
      <button className="primary" onClick={save} disabled={busy}>
        {busy ? "Saving…" : "Save rates"}
      </button>
    </div>
  );
}
