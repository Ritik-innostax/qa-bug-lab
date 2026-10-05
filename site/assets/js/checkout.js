(() => {
  const TAX_RATE_PERCENT = 8.25;
  const rows = [...document.querySelectorAll('#checkout-table tr[data-unit-cents]')];

  function recalculate() {
    let subtotal = 0;
    for (const row of rows) {
      const lineCents = Number(row.dataset.unitCents) * quantityOf(row.querySelector('input'));
      row.querySelector('output').textContent = money(lineCents);
      subtotal += lineCents;
    }
    const tax = Math.round((subtotal * TAX_RATE_PERCENT) / 100);
    document.getElementById('checkout-subtotal').textContent = money(subtotal);
    document.getElementById('checkout-tax').textContent = money(tax);
    document.getElementById('checkout-total').textContent = money(subtotal + tax);
  }

  for (const row of rows) row.querySelector('input').addEventListener('input', recalculate);
  recalculate();
})();
