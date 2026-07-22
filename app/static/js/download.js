const button = document.getElementById('start-download');

button.addEventListener('click', async () => {
  const response = await fetch('/api/download/start', {
    method: 'POST',
  });

  const data = await response.json();

  pollProgress(data.download_id);
});

async function pollProgress(downloadId) {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/download/progress/${downloadId}`);

    const data = await response.json();

    const progress = data.progress;

    document.getElementById('status').textContent = progress.status;

    document.getElementById('received').textContent = progress.received_names;

    document.getElementById('downloaded').textContent = progress.downloaded;

    if (progress.status === 'finished') {
      clearInterval(interval);
    }
  }, 2000);
}
