(() => {
  const rows = [...document.querySelectorAll('#bulk-table tr[data-unit-cents]')];

  function recalculate() {
    let orderTotal = 0;
    for (const row of rows) {
      const unitCents = Number(row.dataset.unitCents);
      const lineCents = unitCents * quantityOf(row.querySelector('input'));
      row.querySelector('output').textContent = money(lineCents);
      orderTotal += unitCents;
    }
    document.getElementById('bulk-total').textContent = money(orderTotal);
  }

  for (const row of rows) row.querySelector('input').addEventListener('input', recalculate);
  recalculate();
})();
