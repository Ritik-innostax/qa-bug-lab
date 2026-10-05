const emailSwitch = document.getElementById('email-switch');
const emailStatus = document.getElementById('email-status');

emailSwitch.addEventListener('click', () => {
  const on = !emailSwitch.getAttribute('aria-checked');
  emailSwitch.setAttribute('aria-checked', String(on));
  emailStatus.textContent = on ? emailSwitch.dataset.onText : emailSwitch.dataset.offText;
});
