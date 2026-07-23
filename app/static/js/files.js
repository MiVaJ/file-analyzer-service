console.log('files.js loaded');

const checkboxes = document.querySelectorAll('input[name="file_ids"]');
console.log('checkboxes:', checkboxes.length);
const statsForm = document.getElementById('stats-form');

const statsButton = statsForm.querySelector('button[type="submit"]');

function updateStatsButton() {
  const selected = document.querySelectorAll('input[name="file_ids"]:checked');

  statsButton.disabled = selected.length === 0;
}

checkboxes.forEach((checkbox) => {
  checkbox.addEventListener('change', updateStatsButton);
});

document.getElementById('select-all').addEventListener('click', () => {
  checkboxes.forEach((checkbox) => {
    checkbox.checked = true;
  });

  updateStatsButton();
});

statsForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const fileIds = [
    ...document.querySelectorAll('input[name="file_ids"]:checked'),
  ].map((input) => Number(input.value));

  const response = await fetch('/api/stats/compute', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      file_ids: fileIds,
    }),
  });

  const data = await response.json();

  renderStats(data);
});

updateStatsButton();

function renderStats(data) {
  const container = document.getElementById('stats-result');

  let html = `
    <h4>Общая статистика</h4>

    <table class="stats-table">
      <thead>
        <tr>
          <th>Цифра</th>
          <th>Количество</th>
        </tr>
      </thead>
      <tbody>
  `;

  for (const [digit, count] of Object.entries(data.total)) {
    html += `
      <tr>
        <td>${digit}</td>
        <td>${count}</td>
      </tr>
    `;
  }

  html += `
      </tbody>
    </table>
  `;

  html += `
    <h4>Статистика файлов</h4>

    <table class="stats-table">
      <thead>
        <tr>
          <th>Файл</th>
          ${Object.keys(data.total)
            .map((digit) => `<th>${digit}</th>`)
            .join('')}
        </tr>
      </thead>
      <tbody>
  `;

  data.files.forEach((file) => {
    html += `
      <tr>
        <td>${file.filename}</td>

        ${Object.values(file.digits)
          .map((count) => `<td>${count}</td>`)
          .join('')}
      </tr>
    `;
  });

  html += `
      </tbody>
    </table>
  `;

  container.innerHTML = html;
}
