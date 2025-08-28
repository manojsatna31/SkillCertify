// static/js/main.js

// Wait for the DOM to be fully loaded before running the script
document.addEventListener("DOMContentLoaded", function () {










  // Find the theme toggle button by its ID
  const themeToggleBtn = document.getElementById("theme-toggle");

  // Check if the button exists on the page to prevent errors
  if (themeToggleBtn) {
    // Add a click event listener to the button
    themeToggleBtn.addEventListener("click", () => {
      // Check if the <html> element currently has the 'dark' class
      const isDarkMode = document.documentElement.classList.contains("dark");

      if (isDarkMode) {
        // If it's currently dark, switch to light mode
        document.documentElement.classList.remove("dark");
        // Save the user's preference in localStorage
        localStorage.setItem("theme", "light");
      } else {
        // If it's currently light, switch to dark mode
        document.documentElement.classList.add("dark");
        // Save the user's preference in localStorage
        localStorage.setItem("theme", "dark");
      }
    });
  }
});

//function jumpToQuestion(absoluteIndex) {
//    const perPage = 10;
//    const page = Math.ceil(absoluteIndex / perPage);
//
//    htmx.ajax('GET', `/exam-report/page/${page}`, {
//        target: '#questions-container',
//        swap: 'innerHTML',
//        // ✅ Use htmx afterSwap event instead of requestAnimationFrame
//        afterSwap: () => {
//            setTimeout(() => {
//                const questionEl = document.getElementById(`question-${absoluteIndex}`);
//                if (questionEl) {
//                    const header = document.querySelector('header');
//                    const headerHeight = header ? header.offsetHeight : 0;
//                    const elementPosition = questionEl.getBoundingClientRect().top + window.pageYOffset;
//                    const offsetPosition = elementPosition - headerHeight - 20;
//
//                    window.scrollTo({
//                        top: offsetPosition,
//                        behavior: 'smooth'
//                    });
//                }
//            }, 50); // tiny delay ensures layout is ready
//        }
//    });
//}

// --- Setup CSS var for sticky header offset
    function updateStickyHeaderVar() {
      const h = document.querySelector('header')?.offsetHeight || 0;
      document.documentElement.style.setProperty('--sticky-header', (h + 16) + 'px');
    }
    window.addEventListener('load', updateStickyHeaderVar);
    window.addEventListener('resize', updateStickyHeaderVar);


// Keep the last requested index so we only scroll for the latest click
//  let pendingJumpIndex = null;
//
//  function jumpToQuestion(absoluteIndex) {
//    const perPage = 10;
//    const page = Math.ceil(absoluteIndex / perPage);
//    pendingJumpIndex = absoluteIndex;
//
//    const target = document.querySelector('#questions-container');
//
//    // Listen once for HTMX finishing the swap of THIS target
//    const onAfterSettle = (evt) => {
//      if (evt.target !== target) return;             // only care about #questions-container swaps
//      document.body.removeEventListener('htmx:afterSettle', onAfterSettle);
//
//      // Highlight the active nav-dot
//  document.querySelectorAll('.nav-dot').forEach(dot => dot.classList.remove('active'));
//  const activeDot = document.querySelector(`.nav-dot[data-index="${absoluteIndex}"]`);
//  if (activeDot) activeDot.classList.add('active');
//
//      // Ensure DOM & layout are fully ready before measuring/scrolling
//      requestAnimationFrame(() => {
//        const id = `question-${pendingJumpIndex}`;
//        const el = document.getElementById(id);
//        if (!el) return;
//
//        // scroll-margin-top handles sticky header nicely
//        el.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
//
//        // optional: brief highlight so users see where they landed
//        el.classList.add('ring-4','ring-indigo-400','ring-offset-2','ring-offset-transparent');
//        setTimeout(() => el.classList.remove('ring-4','ring-indigo-400','ring-offset-2','ring-offset-transparent'), 900);
//      });
//    };
//
//    document.body.addEventListener('htmx:afterSettle', onAfterSettle);
//    htmx.ajax('GET', `/exam-report/page/${page}`, { target: '#questions-container', swap: 'innerHTML' });
//  }
// Keep the last requested index so we only scroll for the latest click
let pendingJumpIndex = null;

function jumpToQuestion(absoluteIndex, questions_per_page) {
  const perPage = questions_per_page;
  const page = Math.ceil(absoluteIndex / perPage);
  pendingJumpIndex = absoluteIndex;

  const target = document.querySelector('#questions-container');

  // Listen once for HTMX finishing the swap of THIS target
  const onAfterSettle = (evt) => {
    if (evt.target !== target) return; // only care about #questions-container swaps

    // Highlight the active nav-dot
    document.querySelectorAll('#exam_report .nav-dot').forEach(dot => dot.classList.remove('active'));
    const activeDot = document.querySelector(`.nav-dot[data-index="${absoluteIndex}"]`);
    if (activeDot) activeDot.classList.add('active');

    // Ensure DOM & layout are fully ready before measuring/scrolling
    requestAnimationFrame(() => {
      const id = `question-${pendingJumpIndex}`;
      const el = document.getElementById(id);
      if (!el) return;

      // scroll-margin-top handles sticky header nicely
      el.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });

      // optional: brief highlight so users see where they landed
      el.classList.add('ring-4','ring-indigo-400','ring-offset-2','ring-offset-transparent');
      setTimeout(() => el.classList.remove('ring-4','ring-indigo-400','ring-offset-2','ring-offset-transparent'), 900);
    });
  };

  // Attach listener only once
  document.body.addEventListener('htmx:afterSettle', onAfterSettle, { once: true });

  // Trigger page load
  htmx.ajax('GET', `/exam-report/page/${page}`, {
    target: '#questions-container',
    swap: 'innerHTML'
  });
}
// Highlight active nav-dot
function setActiveDot(index) {
  document.querySelectorAll('#exam_report .nav-dot').forEach(dot =>
    dot.classList.remove('active')
  );
  const active = document.querySelector(`#exam_report .nav-dot[data-index="${index}"]`);
  if (active) active.classList.add('active');
}

// Watch visible questions
function observeQuestions() {
  const container = document.getElementById('questions-container');
  if (!container) return;

  // Disconnect old observers if re-rendered
  if (window.questionObserver) {
    window.questionObserver.disconnect();
  }

  const options = {
    root: container,             // scrollable container
    rootMargin: '0px 0px -70% 0px', // triggers when top 30% visible
    threshold: 0
  };

  window.questionObserver = new IntersectionObserver((entries) => {
    // Find the first question that is intersecting
    const visible = entries.find(e => e.isIntersecting);
    if (visible) {
      const id = visible.target.id; // e.g. "question-12"
      const index = id.split('-')[1];
      setActiveDot(index);
    }
  }, options);

  // Observe each question card inside container
  container.querySelectorAll('.question-card').forEach(q =>
    window.questionObserver.observe(q)
  );
}

// Call after each HTMX swap so new questions are tracked
document.body.addEventListener('htmx:afterSwap', (evt) => {
  if (evt.target.id === 'questions-container') {
    observeQuestions();
  }
  // Example: stay where you are OR scroll smoothly to top
      if (evt.target.id === "content-area") {
        // Stay at current scroll
        // (remove next line if you don't want auto-scroll at all)
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
});

// Run once initially
observeQuestions();

/*function jumpToQuestion(absoluteIndex) {
    const perPage = 10;
    const page = Math.ceil(absoluteIndex / perPage);

    htmx.ajax('GET', `/exam-report/page/${page}`, {
        target: '#questions-container',
        swap: 'innerHTML',
        afterSwap: () => {
            setTimeout(() => {
                const questionEl = document.getElementById(`question-${absoluteIndex}`);
                if (questionEl) {
                    questionEl.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start',
                        inline: 'nearest'
                    });
                }
            }, 50);
        }
    });
}*/

