function loadCodes() {
  fetch('/api/codes')
    .then(res => res.json())
    .then(data => {
      const table = document.querySelector('#codes-table-body');
      if (!table) return;
      table.innerHTML = '';
      data.forEach(code => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${code.id}</td>
          <td>${code.code}</td>
          <td>${code.used ? 'Yes' : 'No'}</td>
          <td>${code.expires_at}</td>
          <td>
            <form method="POST" action="/delete-code/${code.id}" style="display:inline;">
              <button type="submit" onclick="return confirm('Delete this code?')">🗑️</button>
            </form>
            ${code.used ? `
            <form method="POST" action="/reset-code/${code.id}" style="display:inline;">
              <button type="submit" onclick="return confirm('Reset this code to unused?')">♻️</button>
            </form>` : ''}
            <form method="POST" action="/extend-code/${code.id}" style="display:inline;">
              <button type="submit" onclick="return confirm('Extend this code\'s expiry?')">⏳</button>
            </form>
          </td>
        `;
        table.appendChild(tr);
      });
    });
}

function loadRegistrations() {
  fetch('/api/registrations')
    .then(res => res.json())
    .then(data => {
      const table = document.querySelector('#registrations-table-body');
      if (!table) return;
      table.innerHTML = '';
      data.forEach(reg => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${reg.id}</td>
          <td>${reg.name}</td>
          <td>${reg.email}</td>
          <td>${reg.code}</td>
        `;
        table.appendChild(tr);
      });
    });
}

// Auto-refresh every 10 seconds
setInterval(() => {
  loadCodes();
  loadRegistrations();
}, 10000);

window.onload = () => {
  loadCodes();
  loadRegistrations();
};

console.log("Admin live update script running...");