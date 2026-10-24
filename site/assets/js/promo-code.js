(() => {
  const SUBTOTAL_CENTS = 3750;
  const codeInput = document.getElementById('promo-code');
  const applyButton = document.getElementById('promo-apply');
  const discountOutput = document.getElementById('promo-discount');
  const taxOutput = document.getElementById('promo-tax');
  const totalOutput = document.getElementById('promo-total');

  function recalculate() {
    const discountCents = codeInput.value.trim().toUpperCase() === 'SAVE10'
      ? Math.round((SUBTOTAL_CENTS * 10) / 100)
      : 0;
    // BUG: the tax is worked out on the subtotal before the discount is taken off
    const taxCents = Math.round((SUBTOTAL_CENTS * 8.25) / 100);
    discountOutput.textContent = money(discountCents);
    taxOutput.textContent = money(taxCents);
    totalOutput.textContent = money(SUBTOTAL_CENTS - discountCents + taxCents);
  }

  codeInput.addEventListener('input', recalculate);
  applyButton.addEventListener('click', recalculate);
  recalculate();
})();
