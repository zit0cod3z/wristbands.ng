// WristbandsNG – Main JS

document.addEventListener('DOMContentLoaded', function () {

  // Auto-update copyright year
  const yearEl = document.getElementById('footerYear');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Auto-dismiss toasts
  document.querySelectorAll('.toast').forEach(function (el) {
    setTimeout(function () {
      const toast = bootstrap.Toast.getOrCreateInstance(el);
      toast.hide();
    }, 4000);
  });

  // Navbar scroll effect
  const navbar = document.querySelector('.ep-navbar');
  if (navbar) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 50) {
        navbar.style.background = 'rgba(15,15,26,0.98)';
        navbar.style.boxShadow = '0 4px 20px rgba(0,0,0,0.4)';
      } else {
        navbar.style.background = 'rgba(15,15,26,0.85)';
        navbar.style.boxShadow = 'none';
      }
    });
  }

  // Animate elements on scroll
  const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate__animated', 'animate__fadeInUp');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.ep-event-card').forEach(function (el) {
    observer.observe(el);
  });

});
