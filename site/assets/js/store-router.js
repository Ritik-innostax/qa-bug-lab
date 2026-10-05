// Client-side routing for the store menu.
const STORE_ROUTES = {
  pricing: '/careers/',
  careers: '/careers/',
};

for (const link of document.querySelectorAll('nav[data-router] a[data-route]')) {
  link.addEventListener('click', (event) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    window.location.assign(STORE_ROUTES[link.dataset.route] || link.href);
  });
}
