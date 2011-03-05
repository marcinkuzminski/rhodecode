"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
import random
import hashlib
import StringIO
import urllib

from pygments.formatters import HtmlFormatter
from pygments import highlight as code_highlight
from pylons import url, request
from pylons.i18n.translation import _, ungettext

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
from webhelpers.paginate import Page
from webhelpers.html.tags import _set_input_attrs, _set_id_attr, \
    convert_boolean_attrs, NotGiven

from vcs.utils.annotate import annotate_highlight
from rhodecode.lib.utils import repo_name_slug

def _reset(name, value=None, id=NotGiven, type="reset", **attrs):
    """Reset button
    """
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

class _GetError(object):
    """Get error from form_errors, and represent it as span wrapped error
    message
    
    :param field_name: field to fetch errors for
    :param form_errors: form errors dict
    """

    def __call__(self, field_name, form_errors):
        tmpl = """<span class="error_msg">%s</span>"""
        if form_errors and form_errors.has_key(field_name):
            return literal(tmpl % form_errors.get(field_name))

get_error = _GetError()

class _ToolTip(object):

    def __call__(self, tooltip_title, trim_at=50):
        """Special function just to wrap our text into nice formatted 
        autowrapped text
        
        :param tooltip_title:
        """

        return wrap_paragraphs(escape(tooltip_title), trim_at)\
                       .replace('\n', '<br/>')

    def activate(self):
        """Adds tooltip mechanism to the given Html all tooltips have to have 
        set class `tooltip` and set attribute `tooltip_title`.
        Then a tooltip will be generated based on that. All with yui js tooltip
        """

        js = '''
        YAHOO.util.Event.onDOMReady(function(){
            function toolTipsId(){
                var ids = [];
                var tts = YAHOO.util.Dom.getElementsByClassName('tooltip');
                
                for (var i = 0; i < tts.length; i++) {
                    //if element doesn't not have and id autogenerate one for tooltip
                    
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
            
            // Set the text for the tooltip just before we display it. Lazy method
            myToolTips.contextTriggerEvent.subscribe( 
                 function(type, args) { 

                        var context = args[0]; 
                        
                        //positioning of tooltip
                        var tt_w = this.element.clientWidth;//tooltip width
                        var tt_h = this.element.clientHeight;//tooltip height
                        
                        var context_w = context.offsetWidth;
                        var context_h = context.offsetHeight;
                        
                        var pos_x = YAHOO.util.Dom.getX(context);
                        var pos_y = YAHOO.util.Dom.getY(context);

                        var display_strategy = 'right';
                        var xy_pos = [0,0];
                        switch (display_strategy){
                        
                            case 'top':
                                var cur_x = (pos_x+context_w/2)-(tt_w/2);
                                var cur_y = (pos_y-tt_h-4);
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
        if isinstance(paths, str):
            paths = paths.decode('utf-8', 'replace')
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
    """My code Html Formatter for source codes
    """

    def wrap(self, source, outfile):
        return self._wrap_div(self._wrap_pre(self._wrap_code(source)))

    def _wrap_code(self, source):
        for cnt, it in enumerate(source):
            i, t = it
            t = '<div id="L%s">%s</div>' % (cnt + 1, t)
            yield i, t

    def _wrap_tablelinenos(self, inner):
        dummyoutfile = StringIO.StringIO()
        lncount = 0
        for t, line in inner:
            if t:
                lncount += 1
            dummyoutfile.write(line)

        fl = self.linenostart
        mw = len(str(lncount + fl - 1))
        sp = self.linenospecial
        st = self.linenostep
        la = self.lineanchors
        aln = self.anchorlinenos
        nocls = self.noclasses
        if sp:
            lines = []

            for i in range(fl, fl + lncount):
                if i % st == 0:
                    if i % sp == 0:
                        if aln:
                            lines.append('<a href="#%s%d" class="special">%*d</a>' %
                                         (la, i, mw, i))
                        else:
                            lines.append('<span class="special">%*d</span>' % (mw, i))
                    else:
                        if aln:
                            lines.append('<a href="#%s%d">%*d</a>' % (la, i, mw, i))
                        else:
                            lines.append('%*d' % (mw, i))
                else:
                    lines.append('')
            ls = '\n'.join(lines)
        else:
            lines = []
            for i in range(fl, fl + lncount):
                if i % st == 0:
                    if aln:
                        lines.append('<a href="#%s%d">%*d</a>' % (la, i, mw, i))
                    else:
                        lines.append('%*d' % (mw, i))
                else:
                    lines.append('')
            ls = '\n'.join(lines)

        # in case you wonder about the seemingly redundant <div> here: since the
        # content in the other cell also is wrapped in a div, some browsers in
        # some configurations seem to mess up the formatting...
        if nocls:
            yield 0, ('<table class="%stable">' % self.cssclass +
                      '<tr><td><div class="linenodiv" '
                      'style="background-color: #f0f0f0; padding-right: 10px">'
                      '<pre style="line-height: 125%">' +
                      ls + '</pre></div></td><td class="code">')
        else:
            yield 0, ('<table class="%stable">' % self.cssclass +
                      '<tr><td class="linenos"><div class="linenodiv"><pre>' +
                      ls + '</pre></div></td><td class="code">')
        yield 0, dummyoutfile.getvalue()
        yield 0, '</td></tr></table>'


def pygmentize(filenode, **kwargs):
    """pygmentize function using pygments
    
    :param filenode:
    """

    return literal(code_highlight(filenode.content,
                                  filenode.lexer, CodeHtmlFormatter(**kwargs)))

def pygmentize_annotation(filenode, **kwargs):
    """pygmentize function for annotation
    
    :param filenode:
    """

    color_dict = {}
    def gen_color(n=10000):
        """generator for getting n of evenly distributed colors using 
        hsv color and golden ratio. It always return same order of colors
        
        :returns: RGB tuple
        """
        import colorsys
        golden_ratio = 0.618033988749895
        h = 0.22717784590367374

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
                title=tooltip_html
              )

        uri += '\n'
        return uri
    return literal(annotate_highlight(filenode, url_func, **kwargs))

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


def is_following_repo(repo_name, user_id):
    from rhodecode.model.scm import ScmModel
    return ScmModel().is_following_repo(repo_name, user_id)

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
    """Returns True/False values represented as small html image of true/false
    icons
    
    :param value: bool value
    """

    if value is True:
        return HTML.tag('img', src=url("/images/icons/accept.png"),
                        alt=_('True'))

    if value is False:
        return HTML.tag('img', src=url("/images/icons/cancel.png"),
                        alt=_('False'))

    return value


def action_parser(user_log, feed=False):
    """This helper will action_map the specified string action into translated
    fancy names with icons and links
    
    :param user_log: user log instance
    :param feed: use output for feeds (no html and fancy icons)
    """

    action = user_log.action
    action_params = ' '

    x = action.split(':')

    if len(x) > 1:
        action, action_params = x

    def get_cs_links():
        revs_limit = 5 #display this amount always
        revs_top_limit = 50 #show upto this amount of changesets hidden
        revs = action_params.split(',')
        repo_name = user_log.repository.repo_name

        from rhodecode.model.scm import ScmModel
        repo, dbrepo = ScmModel().get(repo_name, retval='repo',
                                      invalidation_list=[])

        message = lambda rev: get_changeset_safe(repo, rev).message

        cs_links = " " + ', '.join ([link_to(rev,
                url('changeset_home',
                repo_name=repo_name,
                revision=rev), title=tooltip(message(rev)),
                class_='tooltip') for rev in revs[:revs_limit] ])

        compare_view = (' <div class="compare_view tooltip" title="%s">'
                        '<a href="%s">%s</a> '
                        '</div>' % (_('Show all combined changesets %s->%s' \
                                      % (revs[0], revs[-1])),
                                    url('changeset_home', repo_name=repo_name,
                                        revision='%s...%s' % (revs[0], revs[-1])
                                    ),
                                    _('compare view'))
                        )

        if len(revs) > revs_limit:
            uniq_id = revs[0]
            html_tmpl = ('<span> %s '
            '<a class="show_more" id="_%s" href="#more">%s</a> '
            '%s</span>')
            if not feed:
                cs_links += html_tmpl % (_('and'), uniq_id, _('%s more') \
                                        % (len(revs) - revs_limit),
                                        _('revisions'))

            if not feed:
                html_tmpl = '<span id="%s" style="display:none"> %s </span>'
            else:
                html_tmpl = '<span id="%s"> %s </span>'

            cs_links += html_tmpl % (uniq_id, ', '.join([link_to(rev,
                url('changeset_home',
                repo_name=repo_name, revision=rev),
                title=message(rev), class_='tooltip')
                for rev in revs[revs_limit:revs_top_limit]]))
        if len(revs) > 1:
            cs_links += compare_view
        return cs_links

    def get_fork_name():
        repo_name = action_params
        return _('fork name ') + str(link_to(action_params, url('summary_home',
                                          repo_name=repo_name,)))

    action_map = {'user_deleted_repo':(_('[deleted] repository'), None),
           'user_created_repo':(_('[created] repository'), None),
           'user_forked_repo':(_('[forked] repository'), get_fork_name),
           'user_updated_repo':(_('[updated] repository'), None),
           'admin_deleted_repo':(_('[delete] repository'), None),
           'admin_created_repo':(_('[created] repository'), None),
           'admin_forked_repo':(_('[forked] repository'), None),
           'admin_updated_repo':(_('[updated] repository'), None),
           'push':(_('[pushed] into'), get_cs_links),
           'push_remote':(_('[pulled from remote] into'), get_cs_links),
           'pull':(_('[pulled] from'), None),
           'started_following_repo':(_('[started following] repository'), None),
           'stopped_following_repo':(_('[stopped following] repository'), None),
            }

    action_str = action_map.get(action, action)
    if feed:
        action = action_str[0].replace('[', '').replace(']', '')
    else:
        action = action_str[0].replace('[', '<span class="journal_highlight">')\
                   .replace(']', '</span>')

    action_params_func = lambda :""

    if callable(action_str[1]):
        action_params_func = action_str[1]

    return [literal(action), action_params_func]

def action_parser_icon(user_log):
    action = user_log.action
    action_params = None
    x = action.split(':')

    if len(x) > 1:
        action, action_params = x

    tmpl = """<img src="%s%s" alt="%s"/>"""
    map = {'user_deleted_repo':'database_delete.png',
           'user_created_repo':'database_add.png',
           'user_forked_repo':'arrow_divide.png',
           'user_updated_repo':'database_edit.png',
           'admin_deleted_repo':'database_delete.png',
           'admin_created_repo':'database_add.png',
           'admin_forked_repo':'arrow_divide.png',
           'admin_updated_repo':'database_edit.png',
           'push':'script_add.png',
           'push_remote':'connect.png',
           'pull':'down_16.png',
           'started_following_repo':'heart_add.png',
           'stopped_following_repo':'heart_delete.png',
            }
    return literal(tmpl % ((url('/images/icons/')),
                           map.get(action, action), action))


#==============================================================================
# PERMS
#==============================================================================
from rhodecode.lib.auth import HasPermissionAny, HasPermissionAll, \
HasRepoPermissionAny, HasRepoPermissionAll

#==============================================================================
# GRAVATAR URL
#==============================================================================

def gravatar_url(email_address, size=30):
    ssl_enabled = 'https' == request.environ.get('wsgi.url_scheme')
    default = 'identicon'
    baseurl_nossl = "http://www.gravatar.com/avatar/"
    baseurl_ssl = "https://secure.gravatar.com/avatar/"
    baseurl = baseurl_ssl if ssl_enabled else baseurl_nossl

    if isinstance(email_address, unicode):
        #hashlib crashes on unicode items
        email_address = email_address.encode('utf8', 'replace')
    # construct the url
    gravatar_url = baseurl + hashlib.md5(email_address.lower()).hexdigest() + "?"
    gravatar_url += urllib.urlencode({'d':default, 's':str(size)})

    return gravatar_url


#==============================================================================
# REPO PAGER
#==============================================================================
class RepoPage(Page):

    def __init__(self, collection, page=1, items_per_page=20,
        item_count=None, url=None, branch_name=None, **kwargs):

        """Create a "RepoPage" instance. special pager for paging
        repository
        """
        self._url_generator = url

        # Safe the kwargs class-wide so they can be used in the pager() method
        self.kwargs = kwargs

        # Save a reference to the collection
        self.original_collection = collection

        self.collection = collection

        # The self.page is the number of the current page.
        # The first page has the number 1!
        try:
            self.page = int(page) # make it int() if we get it as a string
        except (ValueError, TypeError):
            self.page = 1

        self.items_per_page = items_per_page

        # Unless the user tells us how many items the collections has
        # we calculate that ourselves.
        if item_count is not None:
            self.item_count = item_count
        else:
            self.item_count = len(self.collection)

        # Compute the number of the first and last available page
        if self.item_count > 0:
            self.first_page = 1
            self.page_count = ((self.item_count - 1) / self.items_per_page) + 1
            self.last_page = self.first_page + self.page_count - 1

            # Make sure that the requested page number is the range of valid pages
            if self.page > self.last_page:
                self.page = self.last_page
            elif self.page < self.first_page:
                self.page = self.first_page

            # Note: the number of items on this page can be less than
            #       items_per_page if the last page is not full
            self.first_item = max(0, (self.item_count) - (self.page * items_per_page))
            self.last_item = ((self.item_count - 1) - items_per_page * (self.page - 1))

            iterator = self.collection.get_changesets(start=self.first_item,
                                                      end=self.last_item,
                                                      reverse=True,
                                                      branch_name=branch_name)
            self.items = list(iterator)

            # Links to previous and next page
            if self.page > self.first_page:
                self.previous_page = self.page - 1
            else:
                self.previous_page = None

            if self.page < self.last_page:
                self.next_page = self.page + 1
            else:
                self.next_page = None

        # No items available
        else:
            self.first_page = None
            self.page_count = 0
            self.last_page = None
            self.first_item = None
            self.last_item = None
            self.previous_page = None
            self.next_page = None
            self.items = []

        # This is a subclass of the 'list' type. Initialise the list now.
        list.__init__(self, self.items)


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

def changed_tooltip(nodes):
    if nodes:
        pref = ': <br/> '
        suf = ''
        if len(nodes) > 30:
            suf = '<br/>' + _(' and %s more') % (len(nodes) - 30)
        return literal(pref + '<br/> '.join([x.path.decode('utf-8', 'replace') for x in nodes[:30]]) + suf)
    else:
        return ': ' + _('No Files')
