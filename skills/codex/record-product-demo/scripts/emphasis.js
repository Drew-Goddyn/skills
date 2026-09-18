(() => {
  window.__productDemo?.remove();
  let ring, frame;
  function remove() {
    cancelAnimationFrame(frame);
    ring?.remove();
    ring = null;
  }
  function focus(selector, color) {
    remove();
    const matches = document.querySelectorAll(selector);
    if (matches.length !== 1) throw new Error(`Emphasis needs one target: ${selector}`);
    const target = matches[0];
    ring = document.createElement('div');
    ring.dataset.productDemo = 'focus';
    ring.setAttribute('aria-hidden', 'true');
    ring.setAttribute('popover', 'manual');
    const accent = color || '#448fff';
    ring.style.cssText = `position:fixed;inset:auto;margin:0;padding:0;box-sizing:border-box;pointer-events:none;background:transparent;border:2px solid ${accent};border-radius:8px;opacity:0;transition:opacity 180ms ease;`;
    (target.closest('dialog[open], :popover-open') || document.body).append(ring);
    ring.showPopover();
    function track() {
      if (!target.isConnected || !target.checkVisibility({visibilityProperty:true, opacityProperty:true})) return remove();
      const rect = target.getBoundingClientRect();
      if (rect.bottom <= 0 || rect.top >= innerHeight || rect.right <= 0 || rect.left >= innerWidth) return remove();
      Object.assign(ring.style, {left:`${rect.left - 5}px`, top:`${rect.top - 5}px`, width:`${rect.width + 10}px`, height:`${rect.height + 10}px`, opacity:'1'});
      frame = requestAnimationFrame(track);
    }
    frame = requestAnimationFrame(track);
  }
  window.__productDemo = {focus, remove};
})()
