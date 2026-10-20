const list = document.getElementById('list');
const input = document.getElementById('new-title');
const addButton = document.getElementById('add');
const search = document.getElementById('search');
const counter = document.getElementById('counter');
const stats = document.getElementById('stats');
const statsBody = document.getElementById('stats-body');
let filter = 'all';

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!response.ok) {
    alert('Error ' + response.status);
    throw new Error('HTTP ' + response.status);
  }
  return response.status === 204 ? null : response.json();
}

function render(todos) {
  list.innerHTML = '';
  if (!todos.length) {
    list.innerHTML = '<li class="empty">Nothing here.</li>';
    return;
  }
  for (const todo of todos) {
    const item = document.createElement('li');
    item.className = todo.done ? 'done' : '';
    const box = document.createElement('input');
    box.type = 'checkbox';
    box.checked = todo.done;
    box.setAttribute('aria-label', 'Done');
    box.addEventListener('change', async () => {
      await api(`/api/todos/${todo.id}`, { method: 'PATCH', body: JSON.stringify({ done: box.checked }) });
      load();
    });
    const title = document.createElement('span');
    title.textContent = todo.title;
    const remove = document.createElement('button');
    remove.className = 'remove';
    remove.textContent = '×';
    remove.addEventListener('click', async () => {
      await api(`/api/todos/${todo.id}`, { method: 'DELETE' });
      load();
    });
    item.append(box, title, remove);
    list.append(item);
  }
}

async function load() {
  const todos = await api(`/api/todos?q=${encodeURIComponent(search.value)}&status=${filter}`);
  render(todos);
  const all = await api('/api/todos');
  const left = all.filter(t => t.done).length;
  counter.textContent = `${left} items left`;
}

addButton.addEventListener('click', async () => {
  await api('/api/todos', { method: 'POST', body: JSON.stringify({ title: input.value }) });
  input.value = '';
  load();
});

input.addEventListener('keydown', event => {
  if (event.key === 'Enter') addButton.click();
});

search.addEventListener('input', load);

document.querySelectorAll('.filters button').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
    button.classList.add('active');
    filter = button.dataset.filter;
    load();
  });
});

document.getElementById('stats-toggle').addEventListener('click', async () => {
  stats.hidden = !stats.hidden;
  if (stats.hidden) return;
  statsBody.innerHTML = '';
  const data = await api('/api/stats');
  statsBody.innerHTML = `<dt>Total</dt><dd>${data.total}</dd><dt>Done</dt><dd>${data.done}</dd>` +
    `<dt>Open</dt><dd>${data.open}</dd>`;
});

document.getElementById('share').addEventListener('click', async () => {
  await api('/api/share', { method: 'POST' });
  alert('Sent!');
});

load();
