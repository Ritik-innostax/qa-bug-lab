(() => {
  const SHIPPING_CENTS = 500;
  const FREE_FROM_CENTS = 5000;
  const subtotalInput = document.getElementById('ship-subtotal');
  const feeOutput = document.getElementById('ship-fee');

  function recalculate() {
    const subtotalCents = Math.round(Number(subtotalInput.value) * 100);
    if (!Number.isFinite(subtotalCents) || subtotalCents < 0) {
      feeOutput.textContent = '—';
      return;
    }
    // BUG: the threshold is compared with '>', so an order of exactly $50.00 pays shipping
    const feeCents = subtotalCents > FREE_FROM_CENTS ? 0 : SHIPPING_CENTS;
    feeOutput.textContent = money(feeCents);
  }

  subtotalInput.addEventListener('input', recalculate);
  recalculate();
})();
