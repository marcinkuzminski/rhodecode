"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
import random
import hashlib
from pygments.formatters import HtmlFormatter
from pygments import highlight as code_highlight
from pylons import url, app_globals as g
from pylons.i18n.translation import _, ungettext
from vcs.utils.annotate import annotate_highlight
from webhelpers.html import literal, HTML, escape
from webhelpers.html.tools import *
from webhelpers.html.builder import make_tag
from webhelpers.html.tags import auto_discovery_link, checkbox, css_classes, \
    end_form, file, form, hidden, image, javascript_link, link_to, link_to_if, \
    link_to_unless, ol, required_legend, select, stylesheet_link, submit, text, \
    password, textarea, title, ul, xml_declaration, radio
from webhelpers.html.tools import auto_link, button_to, highlight, js_obfuscate, \
    mail_to, strip_links, strip_tags, tag_re
from webhelpers.number import format_byte_size, format_bit_size
from webhelpers.pylonslib import Flash as _Flash
from webhelpers.pylonslib.secure_form import secure_form
from webhelpers.text import chop_at, collapse, convert_accented_entities, \
    convert_misc_entities, lchop, plural, rchop, remove_formatting, \
    replace_whitespace, urlify, truncate, wrap_paragraphs
from webhelpers.date import time_ago_in_words

from webhelpers.html.tags import _set_input_attrs, _set_id_attr, \
    convert_boolean_attrs, NotGiven

def _reset(name, value=None, id=NotGiven, type="reset", **attrs):
    _set_input_attrs(attrs, type, name, value)
    _set_id_attr(attrs, id, name)
    convert_boolean_attrs(attrs, ["disabled"])
    return HTML.input(**attrs)

reset = _reset


def get_token():
    """Return the current authentication token, creating one if one doesn't
    already exist.
    """
    token_key = "_authentication_token"
    from pylons import session
    if not token_key in session:
        try:
            token = hashlib.sha1(str(random.getrandbits(128))).hexdigest()
        except AttributeError: # Python < 2.4
            token = hashlib.sha1(str(random.randrange(2 ** 128))).hexdigest()
        session[token_key] = token
        if hasattr(session, 'save'):
            session.save()
    return session[token_key]


#Custom helpers here :)
class _Link(object):
    '''
    Make a url based on label and url with help of url_for
    :param label:name of link    if not defined url is used
    :param url: the url for link
    '''

    def __call__(self, label='', *url_, **urlargs):
        if label is None or '':
            label = url
        link_fn = link_to(label, url(*url_, **urlargs))
        return link_fn

link = _Link()

class _GetError(object):

    def __call__(self, field_name, form_errors):
        tmpl = """<span class="error_msg">%s</span>"""
        if form_errors and form_errors.has_key(field_name):
            return literal(tmpl % form_errors.get(field_name))

get_error = _GetError()

def recursive_replace(str, replace=' '):
    """
    Recursive replace of given sign to just one instance
    :param str: given string
    :param replace:char to find and replace multiple instances
        
    Examples::
    >>> recursive_replace("Mighty---Mighty-Bo--sstones",'-')
    'Mighty-Mighty-Bo-sstones'
    """

    if str.find(replace * 2) == -1:
        return str
    else:
        str = str.replace(replace * 2, replace)
        return recursive_replace(str, replace)

class _ToolTip(object):

    def __call__(self, tooltip_title, trim_at=50):
        """
        Special function just to wrap our text into nice formatted autowrapped
        text
        :param tooltip_title:
        """

        return wrap_paragraphs(escape(tooltip_title), trim_at)\
                       .replace('\n', '<br/>')

    def activate(self):
        """
        Adds tooltip mechanism to the given Html all tooltips have to have 
        set class tooltip and set attribute tooltip_title.
        Then a tooltip will be generated based on that
        All with yui js tooltip
        """

        js = '''
        YAHOO.util.Event.onDOMReady(function(){
            function toolTipsId(){
                var ids = [];
                var tts = YAHOO.util.Dom.getElementsByClassName('tooltip');
                
                for (var i = 0; i < tts.length; i++) {
                    //if element doesn't not have and id autgenerate one for tooltip
                    
                    if (!tts[i].id){
                        tts[i].id='tt'+i*100;
                    }
                    ids.push(tts[i].id);
                }
                return ids        
            };
            var myToolTips = new YAHOO.widget.Tooltip("tooltip", { 
                context: toolTipsId(),
                monitorresize:false,
                xyoffset :[0,0],
                autodismissdelay:300000,
                hidedelay:5,
                showdelay:20,
            });
            
            //Mouse Over event disabled for new repositories since they don't
            //have last commit message
            myToolTips.contextMouseOverEvent.subscribe(
                function(type, args) {
                    var context = args[0];
                    var txt = context.getAttribute('tooltip_title');
                    if(txt){                                       
                        return true;
                    }
                    else{
                        return false;
                    }
                });
            
                            
            // Set the text for the tooltip just before we display it. Lazy method
            myToolTips.contextTriggerEvent.subscribe( 
                 function(type, args) { 

                 
                        var context = args[0]; 
                        
                        var txt = context.getAttribute('tooltip_title');
                        this.cfg.setProperty("text", txt);
                        
                        
                        // positioning of tooltip
                        var tt_w = this.element.clientWidth;
                        var tt_h = this.element.clientHeight;
                        
                        var context_w = context.offsetWidth;
                        var context_h = context.offsetHeight;
                        
                        var pos_x = YAHOO.util.Dom.getX(context);
                        var pos_y = YAHOO.util.Dom.getY(context);

                        var display_strategy = 'top';
                        var xy_pos = [0,0];
                        switch (display_strategy){
                        
                            case 'top':
                                var cur_x = (pos_x+context_w/2)-(tt_w/2);
                                var cur_y = pos_y-tt_h-4;
                                xy_pos = [cur_x,cur_y];                                
                                break;
                            case 'bottom':
                                var cur_x = (pos_x+context_w/2)-(tt_w/2);
                                var cur_y = pos_y+context_h+4;
                                xy_pos = [cur_x,cur_y];                                
                                break;
                            case 'left':
                                var cur_x = (pos_x-tt_w-4);
                                var cur_y = pos_y-((tt_h/2)-context_h/2);
                                xy_pos = [cur_x,cur_y];                                
                                break;
                            case 'right':
                                var cur_x = (pos_x+context_w+4);
                                var cur_y = pos_y-((tt_h/2)-context_h/2);
                                xy_pos = [cur_x,cur_y];                                
                                break;
                             default:
                                var cur_x = (pos_x+context_w/2)-(tt_w/2);
                                var cur_y = pos_y-tt_h-4;
                                xy_pos = [cur_x,cur_y];                                
                                break;                             
                                 
                        }

                        this.cfg.setProperty("xy",xy_pos);

                  });
                  
            //Mouse out 
            myToolTips.contextMouseOutEvent.subscribe(
                function(type, args) {
                    var context = args[0];
                    
                });
        });
        '''
        return literal(js)

tooltip = _ToolTip()

class _FilesBreadCrumbs(object):

    def __call__(self, repo_name, rev, paths):
        url_l = [link_to(repo_name, url('files_home',
                                        repo_name=repo_name,
                                        revision=rev, f_path=''))]
        paths_l = paths.split('/')

        for cnt, p in enumerate(paths_l):
            if p != '':
                url_l.append(link_to(p, url('files_home',
                                            repo_name=repo_name,
                                            revision=rev,
                                            f_path='/'.join(paths_l[:cnt + 1]))))

        return literal('/'.join(url_l))

files_breadcrumbs = _FilesBreadCrumbs()
class CodeHtmlFormatter(HtmlFormatter):

    def wrap(self, source, outfile):
        return self._wrap_div(self._wrap_pre(self._wrap_code(source)))

    def _wrap_code(self, source):
        for cnt, it in enumerate(source):
            i, t = it
            t = '<div id="#S-%s">%s</div>' % (cnt + 1, t)
            yield i, t
def pygmentize(filenode, **kwargs):
    """
    pygmentize function using pygments
    :param filenode:
    """
    return literal(code_highlight(filenode.content,
                                  filenode.lexer, CodeHtmlFormatter(**kwargs)))

def pygmentize_annotation(filenode, **kwargs):
    """
    pygmentize function for annotation
    :param filenode:
    """

    color_dict = {}
    def gen_color():
        """generator for getting 10k of evenly distibuted colors using hsv color
        and golden ratio.
        """
        import colorsys
        n = 10000
        golden_ratio = 0.618033988749895
        h = 0.22717784590367374
        #generate 10k nice web friendly colors in the same order
        for c in xrange(n):
            h += golden_ratio
            h %= 1
            HSV_tuple = [h, 0.95, 0.95]
            RGB_tuple = colorsys.hsv_to_rgb(*HSV_tuple)
            yield map(lambda x:str(int(x * 256)), RGB_tuple)

    cgenerator = gen_color()

    def get_color_string(cs):
        if color_dict.has_key(cs):
            col = color_dict[cs]
        else:
            col = color_dict[cs] = cgenerator.next()
        return "color: rgb(%s)! important;" % (', '.join(col))

    def url_func(changeset):
        tooltip_html = "<div style='font-size:0.8em'><b>Author:</b>" + \
        " %s<br/><b>Date:</b> %s</b><br/><b>Message:</b> %s<br/></div>"

        tooltip_html = tooltip_html % (changeset.author,
                                               changeset.date,
                                               tooltip(changeset.message))
        lnk_format = '%5s:%s' % ('r%s' % changeset.revision,
                                 short_id(changeset.raw_id))
        uri = link_to(
                lnk_format,
                url('changeset_home', repo_name=changeset.repository.name,
                    revision=changeset.raw_id),
                style=get_color_string(changeset.raw_id),
                class_='tooltip',
                tooltip_title=tooltip_html
              )

        uri += '\n'
        return uri
    return literal(annotate_highlight(filenode, url_func, **kwargs))

def repo_name_slug(value):
    """Return slug of name of repository
    This function is called on each creation/modification
    of repository to prevent bad names in repo
    """
    slug = remove_formatting(value)
    slug = strip_tags(slug)

    for c in """=[]\;'"<>,/~!@#$%^&*()+{}|: """:
        slug = slug.replace(c, '-')
    slug = recursive_replace(slug, '-')
    slug = collapse(slug, '-')
    return slug

def get_changeset_safe(repo, rev):
    from vcs.backends.base import BaseRepository
    from vcs.exceptions import RepositoryError
    if not isinstance(repo, BaseRepository):
        raise Exception('You must pass an Repository '
                        'object as first argument got %s', type(repo))

    try:
        cs = repo.get_changeset(rev)
    except RepositoryError:
        from rhodecode.lib.utils import EmptyChangeset
        cs = EmptyChangeset()
    return cs


flash = _Flash()


#==============================================================================
# MERCURIAL FILTERS available via h.
#==============================================================================
from mercurial import util
from mercurial.templatefilters import person as _person



def _age(curdate):
    """turns a datetime into an age string."""

    if not curdate:
        return ''

    from datetime import timedelta, datetime

    agescales = [("year", 3600 * 24 * 365),
                 ("month", 3600 * 24 * 30),
                 ("day", 3600 * 24),
                 ("hour", 3600),
                 ("minute", 60),
                 ("second", 1), ]

    age = datetime.now() - curdate
    age_seconds = (age.days * agescales[2][1]) + age.seconds
    pos = 1
    for scale in agescales:
        if scale[1] <= age_seconds:
            if pos == 6:pos = 5
            return time_ago_in_words(curdate, agescales[pos][0]) + ' ' + _('ago')
        pos += 1

    return _('just now')

age = lambda  x:_age(x)
capitalize = lambda x: x.capitalize()
email = util.email
email_or_none = lambda x: util.email(x) if util.email(x) != x else None
person = lambda x: _person(x)
short_id = lambda x: x[:12]


def bool2icon(value):
    """
    Returns True/False values represented as small html image of true/false
    icons
    :param value: bool value
    """

    if value is True:
        return HTML.tag('img', src="/images/icons/accept.png", alt=_('True'))

    if value is False:
        return HTML.tag('img', src="/images/icons/cancel.png", alt=_('False'))

    return value


def action_parser(user_log):
    """
    This helper will map the specified string action into translated
    fancy names with icons and links
    
    @param action:
    """
    action = user_log.action
    action_params = ' '

    x = action.split(':')

    if len(x) > 1:
        action, action_params = x

    def get_cs_links():
        if action == 'push':
            revs_limit = 5
            revs = action_params.split(',')
            cs_links = " " + ', '.join ([link(rev,
                    url('changeset_home',
                    repo_name=user_log.repository.repo_name,
                    revision=rev)) for rev in revs[:revs_limit] ])
            if len(revs) > revs_limit:
                uniq_id = revs[0]
                html_tmpl = ('<span> %s '
                '<a class="show_more" id="_%s" href="#">%s</a> '
                '%s</span>')
                cs_links += html_tmpl % (_('and'), uniq_id, _('%s more') \
                                            % (len(revs) - revs_limit),
                                            _('revisions'))

                html_tmpl = '<span id="%s" style="display:none"> %s </span>'
                cs_links += html_tmpl % (uniq_id, ', '.join([link(rev,
                    url('changeset_home',
                    repo_name=user_log.repository.repo_name,
                    revision=rev)) for rev in revs[revs_limit:] ]))

            return cs_links
        return ''

    def get_fork_name():
        if action == 'user_forked_repo':
            from rhodecode.model.scm import ScmModel
            repo_name = action_params
            repo = ScmModel().get(repo_name)
            if repo is None:
                return repo_name
            return link_to(action_params, url('summary_home',
                                              repo_name=repo.name,),
                                              title=repo.dbrepo.description)
        return ''
    map = {'user_deleted_repo':_('User [deleted] repository'),
           'user_created_repo':_('User [created] repository'),
           'user_forked_repo':_('User [forked] repository as: %s') % get_fork_name(),
           'user_updated_repo':_('User [updated] repository'),
           'admin_deleted_repo':_('Admin [delete] repository'),
           'admin_created_repo':_('Admin [created] repository'),
           'admin_forked_repo':_('Admin [forked] repository'),
           'admin_updated_repo':_('Admin [updated] repository'),
           'push':_('[Pushed] %s') % get_cs_links(),
           'pull':_('[Pulled]'),
           'started_following_repo':_('User [started following] repository'),
           'stopped_following_repo':_('User [stopped following] repository'),
            }

    action_str = map.get(action, action)
    return literal(action_str.replace('[', '<span class="journal_highlight">')\
                   .replace(']', '</span>'))

def action_parser_icon(user_log):
    action = user_log.action
    action_params = None
    x = action.split(':')

    if len(x) > 1:
        action, action_params = x

    tmpl = """<img src="/images/icons/%s" alt="%s"/>"""
    map = {'user_deleted_repo':'database_delete.png',
           'user_created_repo':'database_add.png',
           'user_forked_repo':'arrow_divide.png',
           'user_updated_repo':'database_edit.png',
           'admin_deleted_repo':'database_delete.png',
           'admin_created_repo':'database_ddd.png',
           'admin_forked_repo':'arrow_divide.png',
           'admin_updated_repo':'database_edit.png',
           'push':'script_add.png',
           'pull':'down_16.png',
           'started_following_repo':'heart_add.png',
           'stopped_following_repo':'heart_delete.png',
            }
    return literal(tmpl % (map.get(action, action), action))


#==============================================================================
# PERMS
#==============================================================================
from rhodecode.lib.auth import HasPermissionAny, HasPermissionAll, \
HasRepoPermissionAny, HasRepoPermissionAll

#==============================================================================
# GRAVATAR URL
#==============================================================================
import hashlib
import urllib
from pylons import request

def gravatar_url(email_address, size=30):
    ssl_enabled = 'https' == request.environ.get('HTTP_X_URL_SCHEME')
    default = 'identicon'
    baseurl_nossl = "http://www.gravatar.com/avatar/"
    baseurl_ssl = "https://secure.gravatar.com/avatar/"
    baseurl = baseurl_ssl if ssl_enabled else baseurl_nossl


    # construct the url
    gravatar_url = baseurl + hashlib.md5(email_address.lower()).hexdigest() + "?"
    gravatar_url += urllib.urlencode({'d':default, 's':str(size)})

    return gravatar_url

def safe_unicode(str):
    """safe unicode function. In case of UnicodeDecode error we try to return
    unicode with errors replace, if this failes we return unicode with 
    string_escape decoding """

    try:
        u_str = unicode(str)
    except UnicodeDecodeError:
        try:
            u_str = unicode(str, 'utf-8', 'replace')
        except UnicodeDecodeError:
            #incase we have a decode error just represent as byte string
            u_str = unicode(str(str).encode('string_escape'))

    return u_str
