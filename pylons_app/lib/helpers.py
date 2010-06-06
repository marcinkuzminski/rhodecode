"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from pygments.formatters import HtmlFormatter
from pygments import highlight as code_highlight
from pylons import url, app_globals as g
from pylons.i18n.translation import _, ungettext
from vcs.utils.annotate import annotate_highlight
from webhelpers.html import literal, HTML, escape
from webhelpers.html.builder import make_tag
from webhelpers.html.tags import auto_discovery_link, checkbox, css_classes, \
    end_form, file, form, hidden, image, javascript_link, link_to, link_to_if, \
    link_to_unless, ol, required_legend, select, stylesheet_link, submit, text, \
    password, textarea, title, ul, xml_declaration
from webhelpers.html.tools import auto_link, button_to, highlight, js_obfuscate, \
    mail_to, strip_links, strip_tags, tag_re
from webhelpers.number import format_byte_size, format_bit_size
from webhelpers.pylonslib import Flash as _Flash
from webhelpers.pylonslib.secure_form import secure_form
from webhelpers.text import chop_at, collapse, convert_accented_entities, \
    convert_misc_entities, lchop, plural, rchop, remove_formatting, \
    replace_whitespace, urlify, truncate


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

def pygmentize(filenode, **kwargs):
    """
    pygmentize function using pygments
    @param filenode:
    """
    return literal(code_highlight(filenode.content, filenode.lexer, HtmlFormatter(**kwargs)))

def pygmentize_annotation(filenode, **kwargs):
    """
    pygmentize function for annotation
    @param filenode:
    """
    
    color_dict = g.changeset_annotation_colors
    def gen_color():
        import random
        return [str(random.randrange(10, 235)) for _ in xrange(3)]
    def get_color_string(cs):
        if color_dict.has_key(cs):
            col = color_dict[cs]
        else:
            color_dict[cs] = gen_color()
            col = color_dict[cs]
        return "color: rgb(%s) ! important;" % (','.join(col))
        
    def url_func(changeset):
        return '%s\n' % (link_to(changeset.raw_id,
        url('changeset_home', repo_name='test', revision=changeset.raw_id),
        title=_('author') + ':%s rev:%s %s' % (changeset.author, changeset.revision,
                                                changeset.message,),
        style=get_color_string(changeset.raw_id)))
           
    return literal(annotate_highlight(filenode, url_func, **kwargs))

def recursive_replace(str, replace=' '):
    """
    Recursive replace of given sign to just one instance
    @param str: given string
    @param replace:char to find and replace multiple instances
        
    Examples::
    >>> recursive_replace("Mighty---Mighty-Bo--sstones",'-')
    'Mighty-Mighty-Bo-sstones'
    """

    if str.find(replace * 2) == -1:
        return str
    else:
        str = str.replace(replace * 2, replace)
        return recursive_replace(str, replace)  
      
def repo_name_slug(value):
    """
    Return slug of name of repository
    """
    slug = urlify(value)
    for c in """=[]\;'"<>,/~!@#$%^&*()+{}|:""":
        slug = slug.replace(c, '-')
    slug = recursive_replace(slug, '-')
    return slug
    
files_breadcrumbs = _FilesBreadCrumbs()
link = _Link()
flash = _Flash()
get_error = _GetError()
