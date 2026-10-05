function setSwitch(toggle, on) {
  toggle.setAttribute('aria-checked', String(on));
  const status = document.getElementById(toggle.dataset.status);
  status.textContent = on ? toggle.dataset.onText : toggle.dataset.offText;
}

const smsSwitch = document.getElementById('sms-switch');
smsSwitch.addEventListener('click', () => {
  const on = smsSwitch.getAttribute('aria-checked') === 'true';
  setSwitch(smsSwitch, !on);
});

for (const trigger of document.querySelectorAll('#account-faq .accordion-trigger')) {
  trigger.addEventListener('click', () => {
    const expanded = trigger.getAttribute('aria-expanded') === 'true';
    const panel = document.getElementById(trigger.getAttribute('aria-controls'));
    trigger.setAttribute('aria-expanded', String(!expanded));
    panel.hidden = expanded;
  });
}
