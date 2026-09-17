const LABELS = { compact: "Compact", standard: "Standard", ev: "EV" };

export default function SlotSection({ type, slots, onSlotClick }) {
  return (
    <div className="section">
      <h2>{LABELS[type]}</h2>
      <div className="grid">
        {slots.map((s) => (
          <button
            key={s.id}
            className={`slot ${s.is_occupied ? "occupied" : "free"}`}
            onClick={() => onSlotClick(s)}
            title={s.is_occupied ? `${s.code} — occupied` : `${s.code} — free`}
            style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
          >
            <span>{s.code}</span>
            {type === 'ev' && (
              <span style={{ fontSize: '0.65em', marginTop: '4px', opacity: 0.9 }}>
                ⚡ {s.is_occupied ? 'In Use' : 'Available'}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
