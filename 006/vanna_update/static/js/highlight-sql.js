// Custom SQL syntax highlighting for highlight.js
// This is a browser-compatible version without Node.js module exports
(function() {
    // Define SQL syntax highlighting
    window.SQL_HIGHLIGHT_DEFINITION = {
        name: 'sql',
        case_insensitive: true,
        illegal: /[<>{}*]/,
        contains: [
            {
                beginKeywords:
                    'select insert update delete create drop alter grant revoke table from where join group by having order union except intersect',
                end: /;/,
                keywords: {
                    keyword:
                        'select insert update delete create drop alter grant revoke table from where join left right inner outer cross lateral group by having order union except intersect case when then else end and or not between in like as distinct limit offset asc desc for all some exists any all union except intersect',
                    literal: 'true false null',
                    built_in:
                        'avg count sum min max cast coalesce current_date current_timestamp concat substring trim to_char to_date extract date_part now'
                },
                contains: [
                    {
                        className: 'string',
                        begin: '\'', end: '\'',
                        contains: [{begin: '\'\''}]
                    },
                    {
                        className: 'string',
                        begin: '"', end: '"',
                        contains: [{begin: '""'}]
                    },
                    {
                        className: 'string',
                        begin: '`', end: '`'
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
                        begin: '/\\*', end: '\\*/'
                    }
                ]
            }
        ]
    };

    // Register the language with highlight.js if available
    if (window.hljs) {
        window.hljs.registerLanguage('sql', function() {
            return window.SQL_HIGHLIGHT_DEFINITION;
        });
    }
})();
