/* ========================================================
   Catzilla Landing Page — main.js
   ======================================================== */

(function () {
  'use strict';

  // ---- Theme Toggle ----
  const themeToggle = document.getElementById('themeToggle');
  const root = document.documentElement;

  function getPreferredTheme() {
    const stored = localStorage.getItem('catzilla-theme');
    if (stored) return stored;
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  function setTheme(theme) {
    root.setAttribute('data-theme', theme);
    localStorage.setItem('catzilla-theme', theme);
  }

  // Apply theme immediately (no flash)
  setTheme(getPreferredTheme());

  themeToggle.addEventListener('click', function () {
    const current = root.getAttribute('data-theme');
    setTheme(current === 'dark' ? 'light' : 'dark');
  });

  // Listen for OS theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
    if (!localStorage.getItem('catzilla-theme')) {
      setTheme(e.matches ? 'dark' : 'light');
    }
  });

  // ---- Mobile Navigation ----
  const hamburger = document.getElementById('navHamburger');
  const navLinks = document.getElementById('navLinks');

  hamburger.addEventListener('click', function () {
    hamburger.classList.toggle('active');
    navLinks.classList.toggle('open');
    document.body.style.overflow = navLinks.classList.contains('open') ? 'hidden' : '';
  });

  // Close mobile nav on link click
  navLinks.querySelectorAll('.nav-link').forEach(function (link) {
    link.addEventListener('click', function () {
      hamburger.classList.remove('active');
      navLinks.classList.remove('open');
      document.body.style.overflow = '';
    });
  });

  // ---- Copy to Clipboard ----
  function setupCopy(buttonId) {
    var btn = document.getElementById(buttonId);
    if (!btn) return;
    btn.addEventListener('click', function () {
      navigator.clipboard.writeText('pip install catzilla').then(function () {
        btn.classList.add('copied');
        setTimeout(function () {
          btn.classList.remove('copied');
        }, 2000);
      });
    });
  }

  setupCopy('installCopy');
  setupCopy('installCopyLg');

  // ---- Scroll Fade Animations ----
  var fadeElements = document.querySelectorAll('.scroll-fade');

  if ('IntersectionObserver' in window) {
    var fadeObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            fadeObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    );

    fadeElements.forEach(function (el) {
      fadeObserver.observe(el);
    });
  } else {
    // Fallback: show everything
    fadeElements.forEach(function (el) {
      el.classList.add('visible');
    });
  }

  // ---- Benchmark Bar Chart Animation ----
  var chartBars = document.querySelectorAll('.chart-bar');
  var perfBars = document.querySelectorAll('.perf-bar');

  function animateBars(bars) {
    if (!('IntersectionObserver' in window)) {
      bars.forEach(function (bar) { bar.classList.add('animated'); });
      return;
    }

    var barObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            // Animate all bars in the same container
            var container = entry.target.closest('.chart-bars, .perf-bar-group');
            if (container) {
              container.querySelectorAll('.chart-bar, .perf-bar').forEach(function (bar) {
                bar.classList.add('animated');
              });
            } else {
              entry.target.classList.add('animated');
            }
            barObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.2 }
    );

    bars.forEach(function (bar) {
      barObserver.observe(bar);
    });
  }

  animateBars(chartBars);
  animateBars(perfBars);

  // ---- Number Counter Animation ----
  function animateCounter(el) {
    var target = parseFloat(el.getAttribute('data-count'));
    var decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
    var duration = 1400;
    var start = 0;
    var startTime = null;

    function easeOut(t) {
      return 1 - Math.pow(1 - t, 3);
    }

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var progress = Math.min((timestamp - startTime) / duration, 1);
      var current = start + (target - start) * easeOut(progress);

      if (decimals > 0) {
        el.textContent = current.toFixed(decimals);
      } else {
        el.textContent = Math.round(current).toLocaleString();
      }

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        if (decimals > 0) {
          el.textContent = target.toFixed(decimals);
        } else {
          el.textContent = target.toLocaleString();
        }
      }
    }

    requestAnimationFrame(step);
  }

  // Observe counter elements
  var counterElements = document.querySelectorAll('[data-count]');

  if ('IntersectionObserver' in window) {
    var counterObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            counterObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.3 }
    );

    counterElements.forEach(function (el) {
      counterObserver.observe(el);
    });
  } else {
    counterElements.forEach(function (el) {
      animateCounter(el);
    });
  }

  // ---- Performance Tab Switcher ----
  var tabs = document.querySelectorAll('.perf-tab');

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      var target = tab.getAttribute('data-tab');

      // Update tabs
      tabs.forEach(function (t) { t.classList.remove('active'); });
      tab.classList.add('active');

      // Update panels
      document.querySelectorAll('.perf-panel').forEach(function (panel) {
        panel.classList.remove('active');
      });
      var panel = document.getElementById('panel-' + target);
      if (panel) {
        panel.classList.add('active');

        // Re-trigger bar animations for the new panel
        panel.querySelectorAll('.perf-bar').forEach(function (bar) {
          bar.classList.remove('animated');
          // Force reflow
          void bar.offsetWidth;
          bar.classList.add('animated');
        });

        // Re-trigger counter animations for the new panel
        panel.querySelectorAll('[data-count]').forEach(function (el) {
          animateCounter(el);
        });
      }
    });
  });

  // ---- Smooth Scroll for Anchor Links ----
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var href = link.getAttribute('href');
      if (href === '#') return;
      var target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        var navHeight = document.getElementById('navbar').offsetHeight;
        var top = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 16;
        window.scrollTo({ top: top, behavior: 'smooth' });
      }
    });
  });

  // ---- Navbar scroll effect ----
  var navbar = document.getElementById('navbar');
  var lastScroll = 0;

  window.addEventListener('scroll', function () {
    var currentScroll = window.pageYOffset;
    if (currentScroll > 50) {
      navbar.style.boxShadow = '0 1px 8px rgba(0,0,0,0.15)';
    } else {
      navbar.style.boxShadow = 'none';
    }
    lastScroll = currentScroll;
  }, { passive: true });

  // ---- Code Comparison Tab Switcher ----
  var compareTabs = document.querySelectorAll('.compare-tab');

  compareTabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      var target = tab.getAttribute('data-compare');

      // Update tabs
      compareTabs.forEach(function (t) { t.classList.remove('active'); });
      tab.classList.add('active');

      // Update panels
      document.querySelectorAll('.compare-panel').forEach(function (panel) {
        panel.classList.remove('active');
      });
      var panel = document.getElementById('compare-' + target);
      if (panel) {
        panel.classList.add('active');
      }
    });
  });

})();
