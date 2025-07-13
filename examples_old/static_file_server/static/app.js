// Catzilla Static Server Demo JavaScript
console.log('🐱 Catzilla Static Server Demo loaded!');
console.log('This JavaScript file is served at C-native speed!');

// Test performance by measuring load times
window.addEventListener('load', function() {
    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
    console.log(`📊 Page load time: ${loadTime}ms`);
    console.log('⚡ Static assets served by C-native server with libuv');
});

// Add some interactivity
document.addEventListener('DOMContentLoaded', function() {
    const stats = document.querySelectorAll('.stat');
    stats.forEach((stat, index) => {
        stat.style.animationDelay = `${index * 0.1}s`;
        stat.style.animation = 'fadeInUp 0.6s ease forwards';
    });
});

// CSS animation keyframes will be added by the browser
const style = document.createElement('style');
style.textContent = `
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
`;
document.head.appendChild(style);
