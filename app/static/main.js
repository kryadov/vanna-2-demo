document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('ask-form');
  const sqlPre = document.getElementById('sql');
  const resultsDiv = document.getElementById('results');

  function renderTable(rows) {
    if (!rows || rows.length === 0) {
      return '<p>No rows</p>';
    }
    const cols = Object.keys(rows[0]);
    const thead = `<thead><tr>${cols.map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr></thead>`;
    const tbody = `<tbody>${rows.map(r => `<tr>${cols.map(c => `<td>${escapeHtml(r[c])}</td>`).join('')}</tr>`).join('')}</tbody>`;
    return `<table>${thead}${tbody}</table>`;
  }

  function escapeHtml(v) {
    if (v === null || v === undefined) return '';
    return String(v)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;');
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    sqlPre.textContent = '';
    resultsDiv.innerHTML = '';

    const question = document.getElementById('question').value.trim();
    const execute = document.getElementById('execute').checked;
    const limit = parseInt(document.getElementById('limit').value || '50', 10);

    if (!question) {
      alert('Please enter a question.');
      return;
    }

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, execute, limit })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Request failed');
      }
      sqlPre.textContent = data.sql || '';
      if (data.rows) {
        resultsDiv.innerHTML = renderTable(data.rows);
      }
    } catch (err) {
      console.error(err);
      sqlPre.textContent = '';
      resultsDiv.innerHTML = `<p class="error">${escapeHtml(err.message || String(err))}</p>`;
    }
  });
});
