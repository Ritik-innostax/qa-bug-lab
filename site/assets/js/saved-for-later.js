const laterItems = ['Camp Stool', 'Head Lamp', 'Rain Poncho'];
const laterList = document.getElementById('later-list');
const laterCount = document.getElementById('later-count');
const laterEmpty = document.getElementById('later-empty');

function renderLater() {
  laterList.replaceChildren(
    ...laterItems.map((name, index) => {
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
  laterCount.textContent = String(laterItems.length);
  laterEmpty.hidden = laterItems.length > 0;
}

laterList.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-position]');
  if (!button) return;
  laterItems.splice(Number(button.dataset.position) - 1, 1);
  renderLater();
});

renderLater();
