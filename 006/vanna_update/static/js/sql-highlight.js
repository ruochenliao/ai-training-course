// Make sure highlight.js is initialized
document.addEventListener('DOMContentLoaded', () => {
    if (window.hljs) {
        console.log('highlight.js loaded successfully');
        // Register SQL language if not already registered
        if (!window.hljs.getLanguage('sql')) {
            window.hljs.registerLanguage('sql', function() {
                return {
                    case_insensitive: true,
                    contains: [
                        {
                            className: 'keyword',
                            begin: '\\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|AND|OR|GROUP|BY|ORDER|LIMIT|OFFSET|HAVING|AS|CASE|WHEN|THEN|ELSE|END|WITH|JOIN|LEFT|RIGHT|INNER|OUTER|FULL|ON|IN|NOT|BETWEEN|IS|NULL|TRUE|FALSE)\\b',
                            relevance: 10
                        },
                        {
                            className: 'string',
                            begin: '\'', end: '\'',
                            contains: [{begin: '\\\\\''}]
                        },
                        {
                            className: 'string',
                            begin: '"', end: '"',
                            contains: [{begin: '\\\\"'}]
                        },
                        {
                            className: 'number',
                            begin: '\\b\\d+(\\.\\d+)?',
                            relevance: 0
                        },
                        {
                            className: 'comment',
                            begin: '--', end: '$'
                        },
                        {
                            className: 'comment',
                            begin: '/\\*', end: '\\*/',
                            contains: ['self']
                        }
                    ]
                };
            });
        }
    } else {
        console.error('highlight.js not loaded');
    }
});
