(() => {
  const GIFT_CENTS = 600;
  const WRAP_CENTS = 400;
  const qtyInput = document.getElementById('gift-qty');
  const lineOutput = document.getElementById('gift-line');
  const totalOutput = document.getElementById('gift-total');
  // BUG: the total is built from the quantity the page loaded with, not the current one
  const loadedCents = GIFT_CENTS * quantityOf(qtyInput);

  function recalculate() {
    lineOutput.textContent = money(GIFT_CENTS * quantityOf(qtyInput));
    totalOutput.textContent = money(loadedCents + WRAP_CENTS);
  }

  qtyInput.addEventListener('input', recalculate);
  recalculate();
})();
