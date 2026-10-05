const contactForm = document.getElementById('contact-form');
const contactResult = document.getElementById('contact-result');

contactForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const fields = contactForm.elements;
  const emailField = fields.namedItem('mail');
  if (!emailField) {
    return;
  }
  const data = {
    name: fields.namedItem('name').value.trim(),
    email: emailField.value.trim(),
    message: fields.namedItem('message').value.trim(),
  };
  const result = await postJson('/api/contact', data);
  if (result.ok) {
    showMessage(contactResult, 'success', `Thanks, ${data.name}. Your message has been sent.`);
    contactForm.reset();
  } else {
    showMessage(contactResult, 'error', result.body.error);
  }
});
