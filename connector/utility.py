'''
Created on Jan 24, 2017

@author: cartiaar
'''

# See PickFunctions.bas in WinGem for various bitmap/icon, string loading functions

TRANSLATIONTABLE = {
    # spaces
    "\u2000": " ",
    "\u2001": " ",
    "\u2002": " ",
    "\u2003": " ",
    "\u2004": " ",
    "\u2005": " ",
    "\u2006": " ",
    "\u2007": " ",
    "\u2008": " ",
    "\u2009": " ",
    "\u200A": " ",
    "\u200B": " ",
    "\u200C": " ",
    "\u200D": " ",
    "\u200E": " ",
    "\u200F": " ",
    # Hyphens
    "\u2010": '-',
    "\u2011": '-',
    "\u2012": '-',
    "\u2013": '-',
    "\u2014": '-',
    "\u2015": '-',
    # single quotes
    "\u2018": "'",
    "\u2019": "'",
    "\u201A": "'",
    "\u201B": "'",
    # double quotes
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u201f": '"'
}


def extractfromdelimiter(buffer: str, position: int, delimiter: str):
    ''' Extract a positional substring, based on a passed in delmiter '''
    if buffer.count(delimiter) >= (position - 1):
        return buffer.split(delimiter)[position - 1]
    else:
        return ""


def unicodetoascii(text: str):
    ''' Converts non-mapped unicode string to ascii '''

    # shortcut jump out if nothing to change
    if not text:
        return text

    for charfrom, charto in TRANSLATIONTABLE.items():
        # convert unicode character to ascii character
        text = text.replace(charfrom, charto)

    return text


def charcount(string: str, characters):
    '''
        Build Count Lambda
        l1 is string, l2 is set
        usage:
            punc_count = charcount(a, string.punctuation)
            char_count = charcount(a, string.ascii_letters)
    '''
    result = list(filter(lambda c: c in characters, string))
    return len(result)
