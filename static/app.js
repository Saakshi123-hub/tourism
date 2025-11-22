const q = (sel) => document.querySelector(sel);

const textarea = q('#query');
const btn = q('#send');
const result = q('#result');
const messageDiv = q('#message');
const detailsDiv = q('#details');
// Optional override for hosting UI separately (e.g., GitHub Pages)
const API_BASE = (typeof window !== 'undefined' && window.API_BASE) ? window.API_BASE : '';

btn.addEventListener('click', async () => {
  const text = (textarea.value || '').trim();
  if (!text) {
    alert('Please enter a query.');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Working...';
  result.classList.remove('hidden');
  messageDiv.textContent = 'Thinking...';
  detailsDiv.innerHTML = '';

  try {
    const res = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    if (!res.ok) throw new Error('Request failed');
    const data = await res.json();

    messageDiv.textContent = data.message || 'No response.';

    const lines = [];
    if (data.place) lines.push(`<div><strong>Place:</strong> ${data.place}</div>`);
    if (data.weather_summary) lines.push(`<div><strong>Weather:</strong> ${data.weather_summary}</div>`);
    if (data.places && data.places.length) {
      lines.push('<div><strong>Suggested places:</strong></div>');
      lines.push('<ul>' + data.places.map(p => `<li>${p}</li>`).join('') + '</ul>');
    }
    detailsDiv.innerHTML = lines.join('\n');
  } catch (err) {
    console.error(err);
    messageDiv.textContent = 'Something went wrong. Please try again.';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Send';
  }
});
