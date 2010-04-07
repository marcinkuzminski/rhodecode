"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from pylons import url
from webhelpers.html import (literal, HTML, escape)
from webhelpers.html.tools import (auto_link, button_to, highlight, js_obfuscate
                                   , mail_to, strip_links, strip_tags, tag_re)
from webhelpers.html.tags import (auto_discovery_link, checkbox, css_classes,
                                  end_form, file, form, hidden, image,
                                  javascript_link, link_to, link_to_if,
                                  link_to_unless, ol, required_legend,
                                  select, stylesheet_link,
                                  submit, text, textarea, title, ul, xml_declaration)
from webhelpers.text import (chop_at, collapse, convert_accented_entities,
                             convert_misc_characters, convert_misc_entities,
                             lchop, plural, rchop, remove_formatting, replace_whitespace,
                             urlify)

from webhelpers.pylonslib import Flash as _Flash
from webhelpers.pylonslib.secure_form import secure_form

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

link = _Link()
flash = _Flash()
get_error = _GetError()
