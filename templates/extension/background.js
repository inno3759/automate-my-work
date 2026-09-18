// Service worker: schedule + fetch + storage. No DOM here.
// Uses the browser's login (cookies) for host_permissions sites.
const PERIOD_MIN = 30;

chrome.runtime.onInstalled.addListener(() => chrome.alarms.create('poll', { periodInMinutes: PERIOD_MIN }));
chrome.alarms.onAlarm.addListener((a) => { if (a.name === 'poll') poll(); });
chrome.action.onClicked.addListener(() => poll(true));

async function poll(manual = false) {
  const { seen = [] } = await chrome.storage.local.get('seen');
  try {
    const r = await fetch('https://example.com/api/todo', { credentials: 'include' });
    if (r.status === 401 || r.status === 403 || r.redirected && /login/.test(r.url)) {
      chrome.action.setBadgeText({ text: '!' });
      if (manual) chrome.notifications.create({ type: 'basic', iconUrl: 'icon.png', title: 'Needs login', message: 'Open the site and log in, then click me again.' });
      return;
    }
    if (!r.ok) throw new Error('server ' + r.status);
    const items = await r.json(); // TODO: shape
    const fresh = items.filter(i => !seen.includes(i.id));
    if (fresh.length) {
      chrome.action.setBadgeText({ text: String(fresh.length) });
      chrome.notifications.create({ type: 'basic', iconUrl: 'icon.png', title: `${fresh.length} new`, message: fresh.map(i => i.title).slice(0, 3).join('\n') });
      await chrome.storage.local.set({ seen: [...seen, ...fresh.map(i => i.id)].slice(-5000) });
    } else if (manual) {
      chrome.action.setBadgeText({ text: '' });
    }
  } catch (e) {
    console.warn('[automation] poll failed (will retry):', e.message); // transport/blocked → next alarm
  }
}

// Content script ↔ worker
chrome.runtime.onMessage.addListener((msg, _s, reply) => {
  if (msg.type === 'do-work') { doWork(msg.items).then(reply); return true; }
});
async function doWork(items) { /* TODO: one request per item, dedupe with storage */ return { ok: items.length }; }
