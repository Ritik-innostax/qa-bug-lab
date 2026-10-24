(() => {
  const amountInput = document.getElementById('small-amount');
  const rateInput = document.getElementById('small-rate');
  const taxOutput = document.getElementById('small-tax');

  function recalculate() {
    const amountCents = Math.round(Number(amountInput.value) * 100);
    const ratePercent = Number(rateInput.value);
    if (!Number.isFinite(amountCents) || amountCents < 0 || !Number.isFinite(ratePercent) || ratePercent < 0) {
      taxOutput.textContent = '—';
      return;
    }
    // BUG: Math.floor drops a half cent; the rule on the page says half up
    taxOutput.textContent = money(Math.floor((amountCents * ratePercent) / 100));
  }

  amountInput.addEventListener('input', recalculate);
  rateInput.addEventListener('input', recalculate);
  recalculate();
})();
