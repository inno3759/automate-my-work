// ==UserScript==
// @name         TODO Task name
// @namespace    automations.local
// @version      1.0.0
// @description  One button on the page that does the repetitive part.
// @match        https://example.com/some/page*
// @grant        GM_setValue
// @grant        GM_getValue
// @run-at       document-idle
// ==/UserScript==

/* Rules: plain fetch() with credentials:'include' reuses the tab's login.
   Never re-implement the page's JS — call the same endpoint the page calls
   (found in the HAR). Mark done items so a second click skips them. */

(function () {
  'use strict';
  const TAG = '[automation]';
  const PREFIX = 'am-'; // never ad/banner/sponsor in ids (ad blockers)

  // ---- UI: one button + status box ----
  const box = document.createElement('div');
  box.id = PREFIX + 'box';
  box.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:2147483647;font:13px system-ui;background:#fff;border:1px solid #ccc;border-radius:8px;padding:10px;box-shadow:0 2px 8px rgba(0,0,0,.2);max-width:320px';
  box.innerHTML = `<button id="${PREFIX}go" style="font-size:14px;padding:6px 12px;cursor:pointer">TODO: Button label</button>
    <div id="${PREFIX}status" style="margin-top:6px;white-space:pre-wrap;max-height:160px;overflow:auto"></div>`;
  document.body.appendChild(box);
  const status = (t) => { document.getElementById(PREFIX + 'status').textContent += t + '\n'; console.log(TAG, t); };

  // ---- data: read rows from the DOM or from the page's own API ----
  function readItems() {
    // TODO: e.g. [...document.querySelectorAll('table tr')].map(tr => ({ key: tr.dataset.id, ... }))
    return [];
  }

  // ---- work: ONE request per item, same endpoint the page uses ----
  async function processItem(item) {
    const r = await fetch('/api/todo', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' /* , 'X-CSRF-Token': token from page */ },
      body: JSON.stringify(item),
    });
    if (r.status === 401 || r.status === 403) throw new Error('logged out? (' + r.status + ')');
    if (!r.ok) throw new Error('server answered ' + r.status);
    return r.json();
  }

  document.getElementById(PREFIX + 'go').addEventListener('click', async (ev) => {
    const btn = ev.currentTarget; btn.disabled = true;
    const done = new Set(GM_getValue('done', []));
    const items = readItems().filter(i => !done.has(i.key));
    status(`${items.length} to do (${done.size} already done)`);
    let ok = 0, fail = 0;
    for (const item of items) {
      try {
        await processItem(item);
        done.add(item.key); GM_setValue('done', [...done].slice(-5000)); ok++;
      } catch (e) { fail++; status(`✗ ${item.key}: ${e.message}`); if (/logged out/.test(e.message)) break; }
      await new Promise(r => setTimeout(r, 500 + Math.random() * 1000)); // politeness
    }
    status(`Finished: ${ok} done, ${fail} failed.`);
    btn.disabled = false;
  });
})();
