"""
This module provides some useful tools for ``vcs`` like annotate/diff html
output. It also includes some internal helpers.
"""
import sys
import time
import datetime


def makedate():
    lt = time.localtime()
    if lt[8] == 1 and time.daylight:
        tz = time.altzone
    else:
        tz = time.timezone
    return time.mktime(lt), tz


def date_fromtimestamp(unixts, tzoffset=0):
    """
    Makes a local datetime object out of unix timestamp

    :param unixts:
    :param tzoffset:
    """

    return datetime.datetime.fromtimestamp(float(unixts))


def safe_unicode(str_, from_encoding=None):
    """
    safe unicode function. Does few trick to turn str_ into unicode

    In case of UnicodeDecode error we try to return it with encoding detected
    by chardet library if it fails fallback to unicode with errors replaced

    :param str_: string to decode
    :rtype: unicode
    :returns: unicode object
    """
    if isinstance(str_, unicode):
        return str_
    if not from_encoding:
        import rhodecode
        DEFAULT_ENCODING = rhodecode.CONFIG.get('default_encoding', 'utf8')
        from_encoding = DEFAULT_ENCODING
    try:
        return unicode(str_)
    except UnicodeDecodeError:
        pass

    try:
        return unicode(str_, from_encoding)
    except UnicodeDecodeError:
        pass

    try:
        import chardet
        encoding = chardet.detect(str_)['encoding']
        if encoding is None:
            raise Exception()
        return str_.decode(encoding)
    except (ImportError, UnicodeDecodeError, Exception):
        return unicode(str_, from_encoding, 'replace')


def safe_str(unicode_, to_encoding=None):
    """
    safe str function. Does few trick to turn unicode_ into string

    In case of UnicodeEncodeError we try to return it with encoding detected
    by chardet library if it fails fallback to string with errors replaced

    :param unicode_: unicode to encode
    :rtype: str
    :returns: str object
    """

    if isinstance(unicode_, str):
        return unicode_
    if not to_encoding:
        import rhodecode
        DEFAULT_ENCODING = rhodecode.CONFIG.get('default_encoding', 'utf8')
        to_encoding = DEFAULT_ENCODING
    try:
        return unicode_.encode(to_encoding)
    except UnicodeEncodeError:
        pass

    try:
        import chardet
        encoding = chardet.detect(unicode_)['encoding']
        print encoding
        if encoding is None:
            raise UnicodeEncodeError()

        return unicode_.encode(encoding)
    except (ImportError, UnicodeEncodeError):
        return unicode_.encode(to_encoding, 'replace')

    return safe_str


def author_email(author):
    """
    returns email address of given author.
    If any of <,> sign are found, it fallbacks to regex findall()
    and returns first found result or empty string

    Regex taken from http://www.regular-expressions.info/email.html
    """
    import re
    r = author.find('>')
    l = author.find('<')

    if l == -1 or r == -1:
        # fallback to regex match of email out of a string
        email_re = re.compile(r"""[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!"""
                              r"""#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z"""
                              r"""0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]"""
                              r"""*[a-z0-9])?""", re.IGNORECASE)
        m = re.findall(email_re, author)
        return m[0] if m else ''

    return author[l + 1:r].strip()


def author_name(author):
    """
    get name of author, or else username.
    It'll try to find an email in the author string and just cut it off
    to get the username
    """

    if not '@' in author:
        return author
    else:
        return author.replace(author_email(author), '').replace('<', '')\
            .replace('>', '').strip()
