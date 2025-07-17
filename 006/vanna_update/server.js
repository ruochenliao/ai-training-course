// Simple development server for the frontend
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 9000;
const STATIC_DIR = path.join(__dirname, 'static');

const MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
};

const server = http.createServer((req, res) => {
    console.log(`${req.method} ${req.url}`);

    // Handle CORS for development
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.statusCode = 204;
        res.end();
        return;
    }

    // Parse URL
    let url = req.url;

    // Default to index.html for root path
    if (url === '/' || url === '') {
        url = '/index.html';
    }

    // Remove query string
    const queryStringIndex = url.indexOf('?');
    if (queryStringIndex !== -1) {
        url = url.substring(0, queryStringIndex);
    }

    // Determine file path
    let filePath;

    // Handle /static/ prefix
    if (url.startsWith('/static/')) {
        // Remove /static/ prefix and serve from static directory
        filePath = path.join(STATIC_DIR, url.substring(8));
    } else {
        filePath = path.join(STATIC_DIR, url);
    }

    // Check if file exists
    fs.access(filePath, fs.constants.F_OK, (err) => {
        if (err) {
            console.error(`File not found: ${filePath}`);
            res.statusCode = 404;
            res.end('File not found');
            return;
        }

        // Get file extension
        const ext = path.extname(filePath);

        // Set content type
        const contentType = MIME_TYPES[ext] || 'application/octet-stream';
        res.setHeader('Content-Type', contentType);

        // Stream file to response
        const fileStream = fs.createReadStream(filePath);
        fileStream.pipe(res);

        fileStream.on('error', (err) => {
            console.error(`Error reading file: ${err}`);
            res.statusCode = 500;
            res.end('Server error');
        });
    });
});

server.listen(PORT, () => {
    console.log(`Development server running at http://localhost:${PORT}/`);
    console.log(`Serving static files from ${STATIC_DIR}`);
});
