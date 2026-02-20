// Auto-dismiss alerts after 5 seconds
const ALERT_DISPLAY_TIME = 5000;
const ALERT_FADE_TIME = 500;

document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = 'opacity 0.5s';
      alert.style.opacity = '0';
      setTimeout(function () { alert.remove(); }, ALERT_FADE_TIME);
    }, ALERT_DISPLAY_TIME);
  });
});
