(function () {
  var STORAGE_KEY = 'gdh_consent'; // 'granted' | 'denied'

  function getStoredConsent() {
    try {
      return window.localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function setStoredConsent(value) {
    try {
      window.localStorage.setItem(STORAGE_KEY, value);
    } catch (e) {
      // ignore - banner will just reappear next visit
    }
  }

  function updateGtagConsent(granted) {
    if (typeof window.gtag !== 'function') return;
    window.gtag('consent', 'update', {
      analytics_storage: granted ? 'granted' : 'denied'
    });
  }

  function showBanner() {
    var banner = document.getElementById('consent-banner');
    if (banner) banner.hidden = false;
  }

  function hideBanner() {
    var banner = document.getElementById('consent-banner');
    if (banner) banner.hidden = true;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var stored = getStoredConsent();

    if (stored === 'granted') {
      updateGtagConsent(true);
    } else if (stored === 'denied') {
      // already denied by default - nothing to do
    } else {
      // no choice made yet
      showBanner();
    }

    var acceptBtn = document.getElementById('consent-accept');
    var rejectBtn = document.getElementById('consent-reject');
    var manageLink = document.getElementById('consent-manage');

    if (acceptBtn) {
      acceptBtn.addEventListener('click', function () {
        setStoredConsent('granted');
        updateGtagConsent(true);
        hideBanner();
      });
    }

    if (rejectBtn) {
      rejectBtn.addEventListener('click', function () {
        setStoredConsent('denied');
        updateGtagConsent(false);
        hideBanner();
      });
    }

    if (manageLink) {
      manageLink.addEventListener('click', function () {
        showBanner();
      });
    }
  });
})();