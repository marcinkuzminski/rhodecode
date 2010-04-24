"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from pylons import url
from pylons.i18n.translation import _, ungettext
from webhelpers.html import (literal, HTML, escape)
from webhelpers.html.builder import make_tag
from webhelpers.html.tools import (auto_link, button_to, highlight, js_obfuscate
                                   , mail_to, strip_links, strip_tags, tag_re)
from webhelpers.html.tags import (auto_discovery_link, checkbox, css_classes,
                                  end_form, file, form, hidden, image,
                                  javascript_link, link_to, link_to_if,
                                  link_to_unless, ol, required_legend,
                                  select, stylesheet_link,
                                  submit, text, password, textarea, title,
                                  ul, xml_declaration)
from webhelpers.text import (chop_at, collapse, convert_accented_entities,
                             convert_misc_entities, lchop, plural, rchop,
                             remove_formatting, replace_whitespace, urlify)

from webhelpers.pylonslib import Flash as _Flash
from webhelpers.pylonslib.secure_form import secure_form

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import guess_lexer
from pygments.lexers import get_lexer_by_name

#Custom helper here :)
class _Link(object):
    '''
    Make a url based on label and url with help of url_for
    @param label:name of link    if not defined url is used
    @param url: the url for link
    '''

    def __call__(self, label='', *url_, **urlargs):
        if label is None or '':
            label = url
        link_fn = link_to(label, url(*url_, **urlargs))
        return link_fn


class _GetError(object):

    def __call__(self, field_name, form_errors):
        tmpl = """<span class="error_msg">%s</span>"""
        if form_errors and form_errors.has_key(field_name):
            return literal(tmpl % form_errors.get(field_name))

class _FileSizeFormat(object):
    """
    Formats the value like a 'human-readable' file size (i.e. 13 KB, 4.1 MB,
    102 bytes, etc).
    """
    def __call__(self, bytes):
        try:
            bytes = float(bytes)
        except TypeError:
            return u"0 bytes"
    
        if bytes < 1024:
            return ungettext("%(size)d byte", "%(size)d bytes", bytes) % {'size': bytes}
        if bytes < 1024 * 1024:
            return _("%.1f KB") % (bytes / 1024)
        if bytes < 1024 * 1024 * 1024:
            return _("%.1f MB") % (bytes / (1024 * 1024))
        return _("%.1f GB") % (bytes / (1024 * 1024 * 1024))



def pygmentize(code, **kwargs):
    '''
    Filter for chunks of html to replace code tags with pygmented code
    '''
    return literal(highlight(code, guess_lexer(code), HtmlFormatter(**kwargs)))



filesizeformat = _FileSizeFormat()
link = _Link()
flash = _Flash()
get_error = _GetError()
