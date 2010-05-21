"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from pylons import url, app_globals as g
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
from webhelpers.number import (format_byte_size, format_bit_size)
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

class _FilesBreadCrumbs(object):
    
    def __call__(self, repo_name, rev, paths):
        url_l = [link_to(repo_name, url('files_home', repo_name=repo_name, revision=rev, f_path=''))]
        paths_l = paths.split('/')
        
        for cnt, p in enumerate(paths_l, 1):
            if p != '':
                url_l.append(link_to(p, url('files_home', repo_name=repo_name, revision=rev, f_path='/'.join(paths_l[:cnt]))))

        return literal(' / '.join(url_l))

def pygmentize(code, **kwargs):
    """
    Filter for chunks of html to replace code tags with pygmented code
    """
    code = code.splitlines()
    _html, _html2 = [], []   
    _html.append("""<table class="code-highlighttable">""")
    _html.append("""<tr>""")
    _html.append("""<td class="linenos">""")
    _html.append("""<div class="linenodiv">""")
    _html.append("""<pre>""")
    for cnt, code in enumerate(code, 1):
        #generete lines nos
        _html.append("""<a id="A%s" href="#A%s">%s</a>\n""" \
                     % (cnt, cnt, cnt))
        #propagate second list with code
        _html2.append("""%s""" % (highlight(code, get_lexer_by_name('python'),
                                       HtmlFormatter(nowrap=True))))        
    _html.append("""</pre>""")
    _html.append("""</div>""")
    _html.append("""</td>""")
    _html.append("""<td class="code">""")
    _html.append("""<div class="code-highlight">""")
    _html.append("""<pre>""")
    _html.extend(_html2)
    _html.append("""</pre>""")
    _html.append("""</div>""")
    _html.append("""</td>""")
    _html.append("""</tr>""")
    _html.append("""</table>""")
    return literal(''.join(_html))    
    #return literal(highlight(code, get_lexer_by_name('python'), HtmlFormatter(**kwargs)))

def pygmentize_annotation(annotate_list, repo_name):
    """
    Generate a dict of
    @param annotate_lists:
    """
    import random
    color_dict = g.changeset_annotation_colors
    def gen_color():
            return [str(random.randrange(0, 255)) for _ in xrange(3)]
    def get_color_string(cs):
        if color_dict.has_key(cs):
            col = color_dict[cs]
        else:
            color_dict[cs] = gen_color()
            col = color_dict[cs]
        return "color: rgb(%s) ! important;" % (','.join(col))
    _html, _html2, _html3 = [], [], []   
    _html.append("""<table class="code-highlighttable">""")
    _html.append("""<tr>""")
    _html.append("""<td class="linenos">""")
    _html.append("""<div class="linenodiv">""")
    _html.append("""<pre>""")
    for line in annotate_list:
        #lines
        _html.append("""<a id="A%s" href="#S%s">%s</a>\n""" \
                     % (line[0], line[0], line[0]))
        #annotation tags
        _html2.append("""%s\n""" % link_to(line[1].raw_id,
        url('changeset_home', repo_name=repo_name, revision=line[1].raw_id),
        title=_('author') + ':%s rev:%s %s' % (line[1].author, line[1].revision,
                                                line[1].message,),
        style=get_color_string(line[1].raw_id)))
        #code formated with pygments
        _html3.append("""%s""" % (highlight(line[2], get_lexer_by_name('python')
                                            , HtmlFormatter(nowrap=True))))        
    _html.append("""</pre>""")
    _html.append("""</div>""")
    _html.append("""</td>""")
    _html.append("""<td class="linenos">""")
    _html.append("""<div class="linenodiv">""")                            
    _html.append("""<pre>""")
    _html.extend(_html2)
    _html.append("""</pre>""")
    _html.append("""</div>""")
    _html.append("""</td>""")
    _html.append("""<td class="code">""")
    _html.append("""<div class="code-highlight">""")
    _html.append("""<pre>""")
    _html.extend(_html3)
    _html.append("""</pre>""")
    _html.append("""</div>""")
    _html.append("""</td>""")
    _html.append("""</tr>""")
    _html.append("""</table>""")
    return literal(''.join(_html))


files_breadcrumbs = _FilesBreadCrumbs()
link = _Link()
flash = _Flash()
get_error = _GetError()
