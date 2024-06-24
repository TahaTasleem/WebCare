// Create your own language definition here
// You can safely look at other samples without losing modifications.
// Modifications are not saved on browser refresh/close though -- copy often!
return {
    // Set defaultToken to invalid to see what you do not tokenize yet
    defaultToken: 'invalid',

    keywords: [
        'ADDHANDLER', 'ADDRESSOF', 'ANDALSO', 'ALIAS', 'AND', 'ANSI', 'AS', 'ASSEMBLY', 'ATTRIBUTE', 'AUTO', 'BEGIN', 'BOOLEAN', 'BYREF', 'BYTE', 'BYVAL', 'CALL', 'CAPTURING', 'CASE', 'CATCH', 'CBOOL', 'CBYTE', 'CCHAR', 'CDATE', 'CDEC', 'CDBL', 'CHAR', 'CINT', 'CLASS', 'CLNG', 'COBJ', 'COMPARE', 'CONST', 'CONTINUE', 'CONVERT', 'COUNT', 'CRT', 'CSHORT', 'CSNG', 'CSTR', 'CTYPE', 'CURRENCY', 'DATA', 'DATE', 'DCOUNT', 'DEBUG', 'DECIMAL', 'DECLARE', 'DEFAULT', 'DELEGATE', 'DIM', 'DO', 'DOUBLE', 'DOWNCASE', 'EACH', 'ELSE', 'ELSEIF', 'ENCODE', 'END', 'ENUM', 'EQU', 'EQUATE', 'ERASE', 'ERROR', 'EVENT', 'EXECUTE', 'EXIT', 'EXPLICIT', 'FALSE', 'FINALLY', 'FOR', 'FRIEND', 'FUNCTION', 'GET', 'GETTYPE', 'GLOBAL', 'GOSUB', 'GOTO', 'HANDLES', 'IF', 'IMPLEMENT', 'IMPLEMENTS', 'IMPORTS', 'IN', 'INDEX', 'INT', 'INHERITS', 'INTEGER', 'INTERFACE', 'IS', 'LET', 'LIB', 'LIKE', 'LOAD', 'LOCATE', 'LONG', 'LOOP', 'LOWER', 'LSET', 'MAT', 'ME', 'MID', 'MOD', 'MODULE', 'MUSTINHERIT', 'MUSTOVERRIDE', 'MYBASE', 'MYCLASS', 'NAMESPACE', 'NEW', 'NEXT', 'NOT', 'NOTHING', 'NOTINHERITABLE', 'NOTOVERRIDABLE', 'OBJECT', 'ON', 'OPTION', 'OPTIONAL', 'OR', 'ORELSE', 'OVERLOADS', 'OVERRIDABLE', 'OVERRIDES', 'PARAMARRAY', 'PRESERVE', 'PRIVATE', 'PROPERTY', 'PROTECTED', 'PUBLIC', 'RAISE', 'RAISEEVENT', 'READNEXT', 'READONLY', 'REDIM', 'REM', 'REMOVEHANDLER', 'REPEAT', 'RSET', 'RESUME', 'RETURN', 'SELECT', 'SET', 'SHADOWS', 'SHARED', 'SHORT', 'SINGLE', 'STATIC', 'STEP', 'STOP', 'STRING', 'STRUCTURE', 'SUB', 'SYNCLOCK', 'SYSTEM', 'THEN', 'THROW', 'TIME', 'TO', 'TRUE', 'TRY', 'TYPE', 'TYPEOF', 'UNLOAD', 'UNICODE', 'UNTIL', 'UPCASE', 'VARIANT', 'WEND', 'WHEN', 'WHILE', 'WITH', 'WITHEVENTS', 'WRITEONLY', 'XOR'
    ],

    extendedKeywords: [
        'openSocket', 'closeSocket'
    ],

    typeKeywords: [],

    operators: [
        '=', '>', '<', '!', '~', '?', ':', '==', '<=', '>=', '!=',
        '&&', '||', '++', '--', '+', '-', '*', '/', '&', '|', '^', '%',
        '<<', '>>', '>>>', '+=', '-=', '*=', '/=', '&=', '|=', '^=',
        '%=', '<<=', '>>=', '>>>=', '#'
    ],

    // we include these common regular expressions
    symbols: /[=><!~?:&|+\-*\/\^%#]+/,

    // C# style strings
    escapes: /\\(?:[abfnrtv\\"']|x[0-9A-Fa-f]{1,4}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})/,

    ignoreCase: false,

    // The main tokenizer for our languages
    tokenizer: {
        root: [
            // identifiers and keywords
            //[/[a-z_$][\w$]*/, { cases: { '@typeKeywords': 'keyword',
            [/([~!A-Za-z][,A-Za-z_\$\.\-0-9]*)/, {
                cases: {
                    '@typeKeywords': 'keyword',
                    '@keywords': 'keyword',
                    '@extendedKeywords': 'keyword',
                    '!.*': 'keyword',
                    '@default': 'identifier'
                }
            }],
            // Pick @variables/constants/functions
            [/@\S*/, 'keyword'],

            // whitespace
            {
                include: '@whitespace'
            },

            // delimiters and operators
            [/[{}()\[\]]/, '@brackets'],
            [/[<>](?!@symbols)/, '@brackets'],
            [/@symbols/, {
                cases: {
                    '@operators': 'keyword.operators',
                    '@default': ''
                }
            }],

            // @ annotations.
            // As an example, we emit a debugging log message on these tokens.
            // Note: message are supressed during the first load -- change some lines to see them.
            //[/@\s*[a-zA-Z_\$][\w\$]*/, { token: 'annotation', log: 'annotation token: $0' }],

            // numbers
            [/\d*\.\d+([eE][\-+]?\d+)?/, 'number.float'],
            [/0[xX][0-9a-fA-F]+/, 'number.hex'],
            [/\d+/, 'number'],

            // delimiter: after number because of .\d floats
            [/[;,.]/, 'delimiter'],

            // strings
            [/"([^"])*$/, 'string.invalid'], // non-teminated string
            [/'([^'])*$/, 'string.invalid'], // non-teminated string
            [/\\([^\\])*$/, 'string.invalid'], // non-teminated string
            [/"/, {
                token: 'string.quote',
                bracket: '@open',
                next: '@dblstring'
            }],
            [/'/, {
                token: 'string.quote',
                bracket: '@open',
                next: '@sglstring'
            }],
            [/\\/, {
                token: 'string.quote',
                bracket: '@open',
                next: '@slashstring'
            }],

            // characters
            [/'[^\\']'/, 'string'],
            [/(')(@escapes)(')/, ['string', 'string.escape', 'string']],
            [/'/, 'string.invalid']
        ],

        comment: [
            [/\*.*/, 'comment'],
        ],

        dblstring: [
            [/[^"]/, 'string'],
            [/"/, {
                token: 'string.quote',
                bracket: '@close',
                next: '@pop'
            }]
        ],
        sglstring: [
            [/[^'']/, 'string'],
            [/'/, {
                token: 'string.quote',
                bracket: '@close',
                next: '@pop'
            }]
        ],
        slashstring: [
            [/[^\\]/, 'string'],
            [/\\/, {
                token: 'string.quote',
                bracket: '@close',
                next: '@pop'
            }]
        ],

        // This section is poorly named
        whitespace: [
            [/^([ \t\r\n0-9\.]*)(\*.*)$/, ['number', 'comment']],
            [/[ \t\r\n]+/, 'white'],
            [/\/\*/, 'comment', '@comment'],
            [/;\s*\*.*$/, 'comment'],
        ],
    },
};