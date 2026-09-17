export default function StatsBar({ categories }) {
  return (
    <div className="stats">
      {categories.map((c) => (
        <div className="stat-card" key={c.type}>
          <div className="label">{c.type[0].toUpperCase() + c.type.slice(1)} free</div>
          <div className="value">{c.free} / {c.total}</div>
        </div>
      ))}
    </div>
  );
}
