(() => {
  const SUBTOTAL_CENTS = 42000;
  const TAX_PERCENT = 10;
  const paymentInput = document.getElementById('invoice-payment');
  const taxOutput = document.getElementById('invoice-tax');
  const totalOutput = document.getElementById('invoice-total');
  const dueOutput = document.getElementById('invoice-due');

  function recalculate() {
    const taxCents = Math.round((SUBTOTAL_CENTS * TAX_PERCENT) / 100);
    const totalCents = SUBTOTAL_CENTS + taxCents;
    // BUG: the payment entered is never taken off the total
    taxOutput.textContent = money(taxCents);
    totalOutput.textContent = money(totalCents);
    dueOutput.textContent = money(totalCents);
  }

  paymentInput.addEventListener('input', recalculate);
  recalculate();
})();
