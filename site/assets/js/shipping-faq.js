for (const trigger of document.querySelectorAll('#shipping-faq .accordion-trigger')) {
  trigger.addEventListener('click', () => {
    const expanded = trigger.getAttribute('aria-expanded') === 'true';
    const panel = document.getElementById(trigger.getAttribute('aria-controls'));
    trigger.setAttribute('aria-expanded', String(expanded));
    panel.hidden = !expanded;
  });
}
