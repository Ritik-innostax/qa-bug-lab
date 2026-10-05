(() => {
  const priceInput = document.getElementById('tax-price');
  const rateInput = document.getElementById('tax-rate');
  const taxOutput = document.getElementById('tax-amount');
  const totalOutput = document.getElementById('tax-total');

  function recalculate() {
    const priceCents = Math.round(Number(priceInput.value) * 100);
    const ratePercent = parseInt(rateInput.value, 10);
    if (!Number.isFinite(priceCents) || priceCents < 0 || !Number.isFinite(ratePercent) || ratePercent < 0) {
      taxOutput.textContent = '—';
      totalOutput.textContent = '—';
      return;
    }
    const taxCents = Math.round((priceCents * ratePercent) / 100);
    taxOutput.textContent = money(taxCents);
    totalOutput.textContent = money(priceCents + taxCents);
  }

  priceInput.addEventListener('input', recalculate);
  rateInput.addEventListener('input', recalculate);
  recalculate();
})();
