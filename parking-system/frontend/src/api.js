// Central API client — every backend call goes through here so the base
// URL and error handling live in exactly one place.
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  getSlots: (type) => request(`/slots${type ? `?type=${type}` : ""}`),
  getDashboard: () => request("/dashboard"),
  getPricing: () => request("/pricing"),
  updatePricing: (body) => request("/pricing", { method: "PATCH", body: JSON.stringify(body) }),
  checkIn: (plate, vehicle_type, slot_id) =>
    request("/checkin", {
      method: "POST",
      body: JSON.stringify({ plate, vehicle_type, ...(slot_id ? { slot_id } : {}) }),
    }),
  checkOut: (plate) => request(`/checkout?plate=${encodeURIComponent(plate)}`, { method: "POST" }),
  search: (plate) => request(`/search?plate=${encodeURIComponent(plate)}`),
  simulateAnpr: (vehicle_type, plate, slot_id) =>
    request("/simulate/anpr", {
      method: "POST",
      body: JSON.stringify({
        vehicle_type,
        ...(plate ? { plate } : {}),
        ...(slot_id ? { slot_id } : {}),
      }),
    }),
  simulateSensor: (slot_id, occupied, extra = {}) =>
    request("/simulate/sensor", {
      method: "POST",
      body: JSON.stringify({ slot_id, occupied, ...extra }),
    }),
  wsUrl: () => `${BASE_URL.replace(/^http/, "ws")}/ws/dashboard`,
};
