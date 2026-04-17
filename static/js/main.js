/* main.js — Home page animations */

// Animate feature cards on scroll (Intersection Observer)
const cards = document.querySelectorAll('.feature-card');
if ('IntersectionObserver' in window) {
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) e.target.style.opacity = '1';
    });
  }, { threshold: 0.15 });
  cards.forEach(c => io.observe(c));
}
