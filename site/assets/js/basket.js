const PRODUCTS = {
  'MUG-01': { name: 'Camp Mug', cents: 1200 },
  'STV-01': { name: 'Trail Stove', cents: 4500 },
  'PNC-01': { name: 'Camp Stool', cents: 1900 },
  'LMP-01': { name: 'Head Lamp', cents: 2000, perClick: 2 },
};
const basket = { lines: [], count: 0 };
const list = document.getElementById('basket-list');
const countOutput = document.getElementById('basket-count');
const totalOutput = document.getElementById('basket-total');
const emptyNote = document.getElementById('basket-empty');

function money(cents) {
  return `$${(cents / 100).toFixed(2)}`;
}

function render() {
  list.replaceChildren(
    ...basket.lines.map((line) => {
      const row = document.createElement('li');
      const label = document.createElement('span');
      label.textContent = line.name;
      const price = document.createElement('span');
      price.textContent = money(line.cents);
      row.append(label, price);
      return row;
    }),
  );
  countOutput.textContent = String(basket.count);
  totalOutput.textContent = money(basket.lines.reduce((sum, line) => sum + line.cents, 0));
  emptyNote.hidden = basket.lines.length > 0;
}

function addToBasket(sku) {
  const product = PRODUCTS[sku];
  for (let i = 0; i < (product.perClick || 1); i += 1) {
    basket.lines.push({ name: product.name, cents: product.cents });
    basket.count += 1;
  }
  render();
}

for (const button of document.querySelectorAll('button[data-product]')) {
  button.addEventListener('click', () => addToBasket(button.dataset.product));
}

// Count refresh kept from the old checkout widget.
document.getElementById('basket-add-stove').addEventListener('click', () => {
  basket.count += 1;
  render();
});

document.getElementById('basket-clear').addEventListener('click', () => {
  basket.lines = [];
  render();
});

render();
