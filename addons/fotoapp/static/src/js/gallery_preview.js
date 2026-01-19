/** @odoo-module **/
(() => {
  const triggerClass = 'fotoapp-preview-trigger';
  const maxAttempts = 30;
  let attempt = 0;
  let initialized = false;

  const cleanupZoom = (imgEl) => {
    if (imgEl) {
      imgEl.classList.remove('fotoapp-zoomed');
    }
  };

  const getModalAPI = (modalEl, imgEl) => {
    if (window.bootstrap && window.bootstrap.Modal) {
      const modal = new window.bootstrap.Modal(modalEl, { focus: true });
      modalEl.addEventListener('hidden.bs.modal', () => cleanupZoom(imgEl));
      return { show: () => modal.show() };
    }
    if (window.jQuery && window.jQuery.fn && window.jQuery.fn.modal) {
      window.jQuery(modalEl).on('hidden.bs.modal', () => cleanupZoom(imgEl));
      return { show: () => window.jQuery(modalEl).modal('show') };
    }
    return null;
  };

  const initHandlers = () => {
    attempt += 1;

    const modalEl = document.getElementById('fotoappPreviewModal');
    const imgEl = document.getElementById('fotoappPreviewImg');
    if (!modalEl || !imgEl) {
      if (attempt < maxAttempts) {
        return false;
      }
      return true;
    }

    const modal = getModalAPI(modalEl, imgEl);
    if (!modal) {
      if (attempt < maxAttempts) {
        return false;
      }
      return true;
    }

    if (initialized) { return true; }

    document.addEventListener('click', (ev) => {
      const target = ev.target.closest('.' + triggerClass);
      if (!target) { return; }
      ev.preventDefault();
      const src = target.getAttribute('data-preview-src');
      if (!src) { return; }
      imgEl.src = src;
      imgEl.alt = target.getAttribute('data-preview-alt') || '';
      cleanupZoom(imgEl);
      modal.show();
    });

    imgEl.addEventListener('click', () => {
      imgEl.classList.toggle('fotoapp-zoomed');
    });

    initialized = true;
    return true;
  };

  const tryInit = () => {
    if (initHandlers()) { return; }
    if (attempt >= maxAttempts) { return; }
    setTimeout(tryInit, 150);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', tryInit);
  } else {
    tryInit();
  }
})();
