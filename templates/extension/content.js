// Runs in the page: DOM only. Adds one button; asks the worker to do the work.
(() => {
  const PREFIX = 'am-';
  const btn = document.createElement('button');
  btn.id = PREFIX + 'go';
  btn.textContent = 'TODO: Button label';
  btn.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:2147483647;padding:8px 14px;font:14px system-ui;cursor:pointer';
  btn.onclick = async () => {
    btn.disabled = true;
    const items = []; // TODO: read from DOM
    const res = await chrome.runtime.sendMessage({ type: 'do-work', items });
    btn.textContent = `Done: ${res.ok}`;
    btn.disabled = false;
  };
  document.body.appendChild(btn);
})();
