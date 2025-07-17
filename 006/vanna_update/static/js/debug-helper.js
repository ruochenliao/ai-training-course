// Debug helper for the Vanna Text2SQL application
console.log('Debug helper loaded');

// Check if highlight.js is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');
    
    // Check highlight.js
    if (window.hljs) {
        console.log('highlight.js is available');
        console.log('highlight.js version:', window.hljs.versionString);
        console.log('Registered languages:', Object.keys(window.hljs.listLanguages()));
    } else {
        console.error('highlight.js is NOT available');
    }
    
    // Check Plotly
    if (window.Plotly) {
        console.log('Plotly is available');
        console.log('Plotly version:', window.Plotly.version);
    } else {
        console.error('Plotly is NOT available');
    }
    
    // Add a global error handler
    window.addEventListener('error', (event) => {
        console.error('Global error:', event.error);
    });
});
