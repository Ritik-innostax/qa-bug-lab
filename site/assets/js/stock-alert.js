const stockForm = document.getElementById('stock-form');
const stockResult = document.getElementById('stock-result');

stockForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const email = stockForm.elements.namedItem('email').value.trim();
  const result = await postJson('/api/subscribe', { email });
  if (result.ok) {
    showMessage(stockResult, 'success', `Alert set. We'll email ${email} when the Summit Tent is back.`);
    stockForm.reset();
  } else {
    showMessage(stockResult, 'error', result.body.error);
  }
});
