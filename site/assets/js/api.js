// Shared helpers for the form pages.

async function postJson(url, data) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  let body = {};
  try {
    body = await response.json();
  } catch (error) {
    body = { ok: false, error: 'Unexpected response from the server.' };
  }
  return { ok: response.ok && body.ok === true, status: response.status, body };
}

function showMessage(region, kind, text) {
  region.textContent = text;
  region.className = `form-message ${kind}`;
}
