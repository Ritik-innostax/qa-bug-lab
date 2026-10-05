function money(cents) {
  return `$${(cents / 100).toFixed(2)}`;
}

function quantityOf(input) {
  const value = Math.floor(Number(input.value));
  return Number.isFinite(value) && value > 0 ? value : 0;
}
