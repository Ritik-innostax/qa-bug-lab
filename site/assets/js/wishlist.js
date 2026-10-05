const CATALOG = {
  'JKT-01': 'Summit Jacket',
  'BTL-02': 'Trail Bottle',
};
const wishlistCount = document.getElementById('wishlist-count');
const wishlist = [];

for (const button of document.querySelectorAll('button[data-sku]')) {
  button.addEventListener('click', () => {
    const product = CATALOG[button.dataset.sku];
    if (!product) return;
    wishlist.push(product);
    wishlistCount.textContent = String(wishlist.length);
  });
}
