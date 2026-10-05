const newsletterForm = document.getElementById('newsletter-form');
const newsletterResult = document.getElementById('newsletter-result');

newsletterForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const email = newsletterForm.elements.namedItem('email').value.trim();
  await postJson('/api/subscribe', { email });
  showMessage(newsletterResult, 'success', `You're subscribed. Updates will go to ${email}.`);
  newsletterForm.reset();
});
