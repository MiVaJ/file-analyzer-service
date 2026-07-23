const checkboxes = document.querySelectorAll('input[name="file_ids"]');

document.getElementById('select-page').addEventListener('change', (event) => {
  checkboxes.forEach((checkbox) => {
    checkbox.checked = event.target.checked;
  });
});

document.getElementById('select-all').addEventListener('click', async () => {
  const response = await fetch('/api/files/ids');

  const data = await response.json();

  const ids = new Set(data.file_ids);

  checkboxes.forEach((checkbox) => {
    checkbox.checked = ids.has(Number(checkbox.value));
  });
});

document
  .getElementById('stats-form')
  .addEventListener('submit', async (event) => {
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

    document.getElementById('stats-result').textContent = JSON.stringify(
      data,
      null,
      2
    );
  });
