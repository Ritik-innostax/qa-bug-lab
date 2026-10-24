(() => {
  const table = document.getElementById('review-table');
  const totalOutput = document.getElementById('review-total');
  let totalCents = [...table.querySelectorAll('tbody tr')]
    .reduce((sum, row) => sum + Number(row.dataset.lineCents), 0);

  totalOutput.textContent = money(totalCents);

  table.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-remove]');
    if (!button) return;
    const row = button.closest('tr');
    // BUG: takes off the unit price, not the line total (a Pen line is 3 x $1.50 = $4.50)
    totalCents -= Number(row.dataset.unitCents);
    row.remove();
    totalOutput.textContent = money(totalCents);
  });
})();
