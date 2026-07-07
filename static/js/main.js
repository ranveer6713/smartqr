/**
 * Smart QR Attendance System — Main JavaScript
 * Provides: countdown timer, auto-close, form spinners, and UX polish.
 */

'use strict';

/* ============================================================
   COUNTDOWN TIMER
   Used on the QR display page and student attendance form.
   Reads data-seconds attribute from the timer element.
   ============================================================ */
(function initCountdown() {
  const timerEl = document.getElementById('countdownTimer');
  if (!timerEl) return;

  let seconds = parseInt(timerEl.dataset.seconds, 10);
  if (isNaN(seconds) || seconds < 0) seconds = 0;

  function formatTime(secs) {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }

  function updateDisplay() {
    timerEl.textContent = formatTime(seconds);

    // Turn red and pulsing when under 60 seconds
    if (seconds <= 60) {
      timerEl.classList.add('urgent');
    }

    // When timer reaches zero — redirect / reload to show expired state
    if (seconds <= 0) {
      const redirectUrl = timerEl.dataset.expiredUrl;
      if (redirectUrl) {
        window.location.href = redirectUrl;
      } else {
        window.location.reload();
      }
      return;
    }

    seconds--;
    setTimeout(updateDisplay, 1000);
  }

  updateDisplay();
})();


/* ============================================================
   FORM SUBMIT SPINNER
   Shows a loading overlay on all forms to prevent double-submission.
   ============================================================ */
(function initFormSpinner() {
  const overlay = document.getElementById('spinnerOverlay');
  if (!overlay) return;

  document.querySelectorAll('form').forEach(function(form) {
    form.addEventListener('submit', function() {
      // Don't show spinner on logout form (it's instant)
      if (form.classList.contains('no-spinner')) return;
      
      // If HTML5 validation is supported and form is invalid, don't show spinner
      if (typeof form.checkValidity === 'function' && !form.checkValidity()) {
        return;
      }
      
      overlay.classList.add('show');
    });
  });
})();


/* ============================================================
   SUBJECT AUTO-FILL
   When faculty selects a Subject from dropdown, auto-populates
   the subject_name text field.
   ============================================================ */
(function initSubjectAutofill() {
  const subjectSelect = document.getElementById('id_subject');
  const subjectNameInput = document.getElementById('id_subject_name');

  if (!subjectSelect || !subjectNameInput) return;

  subjectSelect.addEventListener('change', function() {
    const selectedOption = this.options[this.selectedIndex];
    const text = selectedOption.text;

    // Only autofill if a real subject is selected (not the blank "---" option)
    if (this.value && text && !subjectNameInput.value) {
      // Extract just the name part (after " — ")
      const parts = text.split('—');
      subjectNameInput.value = parts.length > 1 ? parts[1].trim() : text.trim();
    }
  });
})();


/* ============================================================
   AUTO-DISMISS ALERTS
   Dismisses flash message alerts after 5 seconds.
   ============================================================ */
(function initAlertAutoDismiss() {
  const alerts = document.querySelectorAll('.alert.alert-dismissible');
  alerts.forEach(function(alert) {
    setTimeout(function() {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 5000);
  });
})();


/* ============================================================
   PAGE REFRESH BUTTON
   Simple helper for pages with a "Refresh" button.
   ============================================================ */
const refreshBtn = document.getElementById('refreshBtn');
if (refreshBtn) {
  refreshBtn.addEventListener('click', function() {
    window.location.reload();
  });
}


/* ============================================================
   AUTO PAGE REFRESH (Faculty session detail / QR page)
   Refreshes the page every N seconds (set via data-refresh-interval).
   ============================================================ */
(function initAutoRefresh() {
  const el = document.querySelector('[data-refresh-interval]');
  if (!el) return;

  const interval = parseInt(el.dataset.refreshInterval, 10);
  if (!isNaN(interval) && interval > 0) {
    setTimeout(function() {
      window.location.reload();
    }, interval * 1000);
  }
})();
