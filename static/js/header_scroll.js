
let lastScrollTop = 0;
const header = document.querySelector('.scroll-header');
const scrollContainer = document.getElementById('main-content') || window;
const isWindow = scrollContainer === window;
let ticking = false;
const THRESHOLD = 10; // ignore tiny scrolls
const SHOW_AFTER = 50; // only show fixed header after this scroll amount

if (header) {
  header.classList.remove('fixed-header', 'shadow-md');
}

function getScrollTop() {
  if (isWindow) return window.pageYOffset || document.documentElement.scrollTop;
  return scrollContainer.scrollTop;
}

function onScroll() {
  if (!header) return;
  const scrollTop = getScrollTop();
  const delta = scrollTop - lastScrollTop;

  if (Math.abs(delta) <= THRESHOLD) {
    // do nothing for tiny movements
  } else if (delta > 0) {
    // Scrolling down: let header scroll away (remove fixed)
    header.classList.remove('fixed-header', 'shadow-md');
  } else {
    // Scrolling up: show fixed header if we've scrolled past SHOW_AFTER
    if (scrollTop > SHOW_AFTER) {
      header.classList.add('fixed-header', 'shadow-md');
    } else {
      header.classList.remove('fixed-header', 'shadow-md');
    }
  }

  // At the very top, ensure header is not fixed
  if (scrollTop === 0) {
    header.classList.remove('fixed-header', 'shadow-md');
  }

  lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
  ticking = false;
}

function handleScrollEvent() {
  if (!ticking) {
    window.requestAnimationFrame(onScroll);
    ticking = true;
  }
}

if (header) {
  if (isWindow) {
    window.addEventListener('scroll', handleScrollEvent, { passive: true });
  } else {
    scrollContainer.addEventListener('scroll', handleScrollEvent, { passive: true });
  }
}
