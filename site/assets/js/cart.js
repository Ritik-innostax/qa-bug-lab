const cartItems = ['Blue Mug', 'Red Pen', 'Green Notebook'];
const cartList = document.getElementById('cart-list');
const cartCount = document.getElementById('cart-count');
const cartEmpty = document.getElementById('cart-empty');

function renderCart() {
  cartList.replaceChildren(
    ...cartItems.map((name, index) => {
      const row = document.createElement('li');
      const label = document.createElement('span');
      label.textContent = name;
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'secondary';
      remove.textContent = `Remove ${name}`;
      remove.dataset.position = String(index + 1);
      row.append(label, remove);
      return row;
    }),
  );
  cartCount.textContent = String(cartItems.length);
  cartEmpty.hidden = cartItems.length > 0;
}

cartList.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-position]');
  if (!button) return;
  cartItems.splice(Number(button.dataset.position), 1);
  renderCart();
});

renderCart();
