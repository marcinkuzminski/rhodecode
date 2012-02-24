"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
import random
import hashlib
import StringIO
import urllib
import math
import logging

from datetime import datetime
from pygments.formatters.html import HtmlFormatter
from pygments import highlight as code_highlight
from pylons import url, request, config
from pylons.i18n.translation import _, ungettext
from hashlib import md5

from webhelpers.html import literal, HTML, escape
from webhelpers.html.tools import *
from webhelpers.html.builder import make_tag
from webhelpers.html.tags import auto_discovery_link, checkbox, css_classes, \
    end_form, file, form, hidden, image, javascript_link, link_to, \
    link_to_if, link_to_unless, ol, required_legend, select, stylesheet_link, \
    submit, text, password, textarea, title, ul, xml_declaration, radio
from webhelpers.html.tools import auto_link, button_to, highlight, \
    js_obfuscate, mail_to, strip_links, strip_tags, tag_re
from webhelpers.number import format_byte_size, format_bit_size
from webhelpers.pylonslib import Flash as _Flash
from webhelpers.pylonslib.secure_form import secure_form
from webhelpers.text import chop_at, collapse, convert_accented_entities, \
    convert_misc_entities, lchop, plural, rchop, remove_formatting, \
    replace_whitespace, urlify, truncate, wrap_paragraphs
from webhelpers.date import time_ago_in_words
from webhelpers.paginate import Page
from webhelpers.html.tags import _set_input_attrs, _set_id_attr, \
    convert_boolean_attrs, NotGiven, _make_safe_id_component

from rhodecode.lib.annotate import annotate_highlight
from rhodecode.lib.utils import repo_name_slug
from rhodecode.lib import str2bool, safe_unicode, safe_str, get_changeset_safe
from rhodecode.lib.markup_renderer import MarkupRenderer

log = logging.getLogger(__name__)


def _reset(name, value=None, id=NotGiven, type="reset", **attrs):
    """
    Reset button
    """
    _set_input_attrs(attrs, type, name, value)
    _set_id_attr(attrs, id, name)
    convert_boolean_attrs(attrs, ["disabled"])
    return HTML.input(**attrs)

reset = _reset
safeid = _make_safe_id_component


def FID(raw_id, path):
    """
    Creates a uniqe ID for filenode based on it's hash of path and revision
    it's safe to use in urls

    :param raw_id:
    :param path:
    """

    return 'C-%s-%s' % (short_id(raw_id), md5(path).hexdigest()[:12])


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
        return escape(tooltip_title)
tooltip = _ToolTip()

class _FilesBreadCrumbs(object):

    def __call__(self, repo_name, rev, paths):
        if isinstance(paths, str):
            paths = safe_unicode(paths)
        url_l = [link_to(repo_name, url('files_home',
                                        repo_name=repo_name,
                                        revision=rev, f_path=''))]
        paths_l = paths.split('/')
        for cnt, p in enumerate(paths_l):
            if p != '':
                url_l.append(link_to(p,
                                     url('files_home',
                                         repo_name=repo_name,
                                         revision=rev,
                                         f_path='/'.join(paths_l[:cnt + 1])
                                         )
                                     )
                             )

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
                      ls + '</pre></div></td><td id="hlcode" class="code">')
        else:
            yield 0, ('<table class="%stable">' % self.cssclass +
                      '<tr><td class="linenos"><div class="linenodiv"><pre>' +
                      ls + '</pre></div></td><td id="hlcode" class="code">')
        yield 0, dummyoutfile.getvalue()
        yield 0, '</td></tr></table>'


def pygmentize(filenode, **kwargs):
    """pygmentize function using pygments

    :param filenode:
    """

    return literal(code_highlight(filenode.content,
                                  filenode.lexer, CodeHtmlFormatter(**kwargs)))


def pygmentize_annotation(repo_name, filenode, **kwargs):
    """
    pygmentize function for annotation

    :param filenode:
    """

    color_dict = {}

    def gen_color(n=10000):
        """generator for getting n of evenly distributed colors using
        hsv color and golden ratio. It always return same order of colors

        :returns: RGB tuple
        """

        def hsv_to_rgb(h, s, v):
            if s == 0.0:
                return v, v, v
            i = int(h * 6.0)  # XXX assume int() truncates!
            f = (h * 6.0) - i
            p = v * (1.0 - s)
            q = v * (1.0 - s * f)
            t = v * (1.0 - s * (1.0 - f))
            i = i % 6
            if i == 0:
                return v, t, p
            if i == 1:
                return q, v, p
            if i == 2:
                return p, v, t
            if i == 3:
                return p, q, v
            if i == 4:
                return t, p, v
            if i == 5:
                return v, p, q

        golden_ratio = 0.618033988749895
        h = 0.22717784590367374

        for _ in xrange(n):
            h += golden_ratio
            h %= 1
            HSV_tuple = [h, 0.95, 0.95]
            RGB_tuple = hsv_to_rgb(*HSV_tuple)
            yield map(lambda x: str(int(x * 256)), RGB_tuple)

    cgenerator = gen_color()

    def get_color_string(cs):
        if cs in color_dict:
            col = color_dict[cs]
        else:
            col = color_dict[cs] = cgenerator.next()
        return "color: rgb(%s)! important;" % (', '.join(col))

    def url_func(repo_name):

        def _url_func(changeset):
            author = changeset.author
            date = changeset.date
            message = tooltip(changeset.message)

            tooltip_html = ("<div style='font-size:0.8em'><b>Author:</b>"
                            " %s<br/><b>Date:</b> %s</b><br/><b>Message:"
                            "</b> %s<br/></div>")

            tooltip_html = tooltip_html % (author, date, message)
            lnk_format = '%5s:%s' % ('r%s' % changeset.revision,
                                     short_id(changeset.raw_id))
            uri = link_to(
                    lnk_format,
                    url('changeset_home', repo_name=repo_name,
                        revision=changeset.raw_id),
                    style=get_color_string(changeset.raw_id),
                    class_='tooltip',
                    title=tooltip_html
                  )

            uri += '\n'
            return uri
        return _url_func

    return literal(annotate_highlight(filenode, url_func(repo_name), **kwargs))


def is_following_repo(repo_name, user_id):
    from rhodecode.model.scm import ScmModel
    return ScmModel().is_following_repo(repo_name, user_id)

flash = _Flash()

#==============================================================================
# SCM FILTERS available via h.
#==============================================================================
from rhodecode.lib.vcs.utils import author_name, author_email
from rhodecode.lib import credentials_filter, age as _age
from rhodecode.model.db import User

age = lambda  x: _age(x)
capitalize = lambda x: x.capitalize()
email = author_email
short_id = lambda x: x[:12]
hide_credentials = lambda x: ''.join(credentials_filter(x))


def is_git(repository):
    if hasattr(repository, 'alias'):
        _type = repository.alias
    elif hasattr(repository, 'repo_type'):
        _type = repository.repo_type
    else:
        _type = repository
    return _type == 'git'


def is_hg(repository):
    if hasattr(repository, 'alias'):
        _type = repository.alias
    elif hasattr(repository, 'repo_type'):
        _type = repository.repo_type
    else:
        _type = repository
    return _type == 'hg'


def email_or_none(author):
    _email = email(author)
    if _email != '':
        return _email

    # See if it contains a username we can get an email from
    user = User.get_by_username(author_name(author), case_insensitive=True,
                                cache=True)
    if user is not None:
        return user.email

    # No valid email, not a valid user in the system, none!
    return None


def person(author):
    # attr to return from fetched user
    person_getter = lambda usr: usr.username

    # Valid email in the attribute passed, see if they're in the system
    _email = email(author)
    if _email != '':
        user = User.get_by_email(_email, case_insensitive=True, cache=True)
        if user is not None:
            return person_getter(user)
        return _email

    # Maybe it's a username?
    _author = author_name(author)
    user = User.get_by_username(_author, case_insensitive=True,
                                cache=True)
    if user is not None:
        return person_getter(user)

    # Still nothing?  Just pass back the author name then
    return _author


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
    """
    This helper will action_map the specified string action into translated
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
        revs_limit = 3  # display this amount always
        revs_top_limit = 50  # show upto this amount of changesets hidden
        revs_ids = action_params.split(',')
        deleted = user_log.repository is None
        if deleted:
            return ','.join(revs_ids)

        repo_name = user_log.repository.repo_name

        repo = user_log.repository.scm_instance

        message = lambda rev: rev.message
        lnk = lambda rev, repo_name: (
            link_to('r%s:%s' % (rev.revision, rev.short_id),
                    url('changeset_home', repo_name=repo_name,
                        revision=rev.raw_id),
                    title=tooltip(message(rev)), class_='tooltip')
        )
        # get only max revs_top_limit of changeset for performance/ui reasons
        revs = [
            x for x in repo.get_changesets(revs_ids[0],
                                           revs_ids[:revs_top_limit][-1])
        ]

        cs_links = []
        cs_links.append(" " + ', '.join(
            [lnk(rev, repo_name) for rev in revs[:revs_limit]]
            )
        )

        compare_view = (
            ' <div class="compare_view tooltip" title="%s">'
            '<a href="%s">%s</a> </div>' % (
                _('Show all combined changesets %s->%s') % (
                    revs_ids[0], revs_ids[-1]
                ),
                url('changeset_home', repo_name=repo_name,
                    revision='%s...%s' % (revs_ids[0], revs_ids[-1])
                ),
                _('compare view')
            )
        )

        # if we have exactly one more than normally displayed
        # just display it, takes less space than displaying
        # "and 1 more revisions"
        if len(revs_ids) == revs_limit + 1:
            rev = revs[revs_limit]
            cs_links.append(", " + lnk(rev, repo_name))

        # hidden-by-default ones
        if len(revs_ids) > revs_limit + 1:
            uniq_id = revs_ids[0]
            html_tmpl = (
                '<span> %s <a class="show_more" id="_%s" '
                'href="#more">%s</a> %s</span>'
            )
            if not feed:
                cs_links.append(html_tmpl % (
                      _('and'),
                      uniq_id, _('%s more') % (len(revs_ids) - revs_limit),
                      _('revisions')
                    )
                )

            if not feed:
                html_tmpl = '<span id="%s" style="display:none">, %s </span>'
            else:
                html_tmpl = '<span id="%s"> %s </span>'

            morelinks = ', '.join(
              [lnk(rev, repo_name) for rev in revs[revs_limit:]]
            )

            if len(revs_ids) > revs_top_limit:
                morelinks += ', ...'

            cs_links.append(html_tmpl % (uniq_id, morelinks))
        if len(revs) > 1:
            cs_links.append(compare_view)
        return ''.join(cs_links)

    def get_fork_name():
        repo_name = action_params
        return _('fork name ') + str(link_to(action_params, url('summary_home',
                                          repo_name=repo_name,)))

    action_map = {'user_deleted_repo': (_('[deleted] repository'), None),
           'user_created_repo': (_('[created] repository'), None),
           'user_created_fork': (_('[created] repository as fork'), None),
           'user_forked_repo': (_('[forked] repository'), get_fork_name),
           'user_updated_repo': (_('[updated] repository'), None),
           'admin_deleted_repo': (_('[delete] repository'), None),
           'admin_created_repo': (_('[created] repository'), None),
           'admin_forked_repo': (_('[forked] repository'), None),
           'admin_updated_repo': (_('[updated] repository'), None),
           'push': (_('[pushed] into'), get_cs_links),
           'push_local': (_('[committed via RhodeCode] into'), get_cs_links),
           'push_remote': (_('[pulled from remote] into'), get_cs_links),
           'pull': (_('[pulled] from'), None),
           'started_following_repo': (_('[started following] repository'), None),
           'stopped_following_repo': (_('[stopped following] repository'), None),
            }

    action_str = action_map.get(action, action)
    if feed:
        action = action_str[0].replace('[', '').replace(']', '')
    else:
        action = action_str[0]\
            .replace('[', '<span class="journal_highlight">')\
            .replace(']', '</span>')

    action_params_func = lambda: ""

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
           'user_created_fork':'arrow_divide.png',
           'user_forked_repo':'arrow_divide.png',
           'user_updated_repo':'database_edit.png',
           'admin_deleted_repo':'database_delete.png',
           'admin_created_repo':'database_add.png',
           'admin_forked_repo':'arrow_divide.png',
           'admin_updated_repo':'database_edit.png',
           'push':'script_add.png',
           'push_local':'script_edit.png',
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
    if (not str2bool(config['app_conf'].get('use_gravatar')) or
        not email_address or email_address == 'anonymous@rhodecode.org'):
        f = lambda a, l: min(l, key=lambda x: abs(x - a))
        return url("/images/user%s.png" % f(size, [14, 16, 20, 24, 30]))

    ssl_enabled = 'https' == request.environ.get('wsgi.url_scheme')
    default = 'identicon'
    baseurl_nossl = "http://www.gravatar.com/avatar/"
    baseurl_ssl = "https://secure.gravatar.com/avatar/"
    baseurl = baseurl_ssl if ssl_enabled else baseurl_nossl

    if isinstance(email_address, unicode):
        #hashlib crashes on unicode items
        email_address = safe_str(email_address)
    # construct the url
    gravatar_url = baseurl + hashlib.md5(email_address.lower()).hexdigest() + "?"
    gravatar_url += urllib.urlencode({'d': default, 's': str(size)})

    return gravatar_url


#==============================================================================
# REPO PAGER, PAGER FOR REPOSITORY
#==============================================================================
class RepoPage(Page):

    def __init__(self, collection, page=1, items_per_page=20,
                 item_count=None, url=None, **kwargs):

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
            self.page = int(page)  # make it int() if we get it as a string
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
            self.page_count = int(math.ceil(float(self.item_count) /
                                            self.items_per_page))
            self.last_page = self.first_page + self.page_count - 1

            # Make sure that the requested page number is the range of
            # valid pages
            if self.page > self.last_page:
                self.page = self.last_page
            elif self.page < self.first_page:
                self.page = self.first_page

            # Note: the number of items on this page can be less than
            #       items_per_page if the last page is not full
            self.first_item = max(0, (self.item_count) - (self.page *
                                                          items_per_page))
            self.last_item = ((self.item_count - 1) - items_per_page *
                              (self.page - 1))

            self.items = list(self.collection[self.first_item:self.last_item + 1])

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
        list.__init__(self, reversed(self.items))


def changed_tooltip(nodes):
    """
    Generates a html string for changed nodes in changeset page.
    It limits the output to 30 entries

    :param nodes: LazyNodesGenerator
    """
    if nodes:
        pref = ': <br/> '
        suf = ''
        if len(nodes) > 30:
            suf = '<br/>' + _(' and %s more') % (len(nodes) - 30)
        return literal(pref + '<br/> '.join([safe_unicode(x.path)
                                             for x in nodes[:30]]) + suf)
    else:
        return ': ' + _('No Files')


def repo_link(groups_and_repos):
    """
    Makes a breadcrumbs link to repo within a group
    joins &raquo; on each group to create a fancy link

    ex::
        group >> subgroup >> repo

    :param groups_and_repos:
    """
    groups, repo_name = groups_and_repos

    if not groups:
        return repo_name
    else:
        def make_link(group):
            return link_to(group.name, url('repos_group_home',
                                           group_name=group.group_name))
        return literal(' &raquo; '.join(map(make_link, groups)) + \
                       " &raquo; " + repo_name)


def fancy_file_stats(stats):
    """
    Displays a fancy two colored bar for number of added/deleted
    lines of code on file

    :param stats: two element list of added/deleted lines of code
    """

    a, d, t = stats[0], stats[1], stats[0] + stats[1]
    width = 100
    unit = float(width) / (t or 1)

    # needs > 9% of width to be visible or 0 to be hidden
    a_p = max(9, unit * a) if a > 0 else 0
    d_p = max(9, unit * d) if d > 0 else 0
    p_sum = a_p + d_p

    if p_sum > width:
        #adjust the percentage to be == 100% since we adjusted to 9
        if a_p > d_p:
            a_p = a_p - (p_sum - width)
        else:
            d_p = d_p - (p_sum - width)

    a_v = a if a > 0 else ''
    d_v = d if d > 0 else ''

    def cgen(l_type):
        mapping = {'tr': 'top-right-rounded-corner',
                   'tl': 'top-left-rounded-corner',
                   'br': 'bottom-right-rounded-corner',
                   'bl': 'bottom-left-rounded-corner'}
        map_getter = lambda x: mapping[x]

        if l_type == 'a' and d_v:
            #case when added and deleted are present
            return ' '.join(map(map_getter, ['tl', 'bl']))

        if l_type == 'a' and not d_v:
            return ' '.join(map(map_getter, ['tr', 'br', 'tl', 'bl']))

        if l_type == 'd' and a_v:
            return ' '.join(map(map_getter, ['tr', 'br']))

        if l_type == 'd' and not a_v:
            return ' '.join(map(map_getter, ['tr', 'br', 'tl', 'bl']))

    d_a = '<div class="added %s" style="width:%s%%">%s</div>' % (
        cgen('a'), a_p, a_v
    )
    d_d = '<div class="deleted %s" style="width:%s%%">%s</div>' % (
        cgen('d'), d_p, d_v
    )
    return literal('<div style="width:%spx">%s%s</div>' % (width, d_a, d_d))


def urlify_text(text_):
    import re

    url_pat = re.compile(r'''(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]'''
                         '''|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)''')

    def url_func(match_obj):
        url_full = match_obj.groups()[0]
        return '<a href="%(url)s">%(url)s</a>' % ({'url': url_full})

    return literal(url_pat.sub(url_func, text_))


def urlify_changesets(text_, repository):
    import re
    URL_PAT = re.compile(r'([0-9a-fA-F]{12,})')

    def url_func(match_obj):
        rev = match_obj.groups()[0]
        pref = ''
        if match_obj.group().startswith(' '):
            pref = ' '
        tmpl = (
        '%(pref)s<a class="%(cls)s" href="%(url)s">'
        '%(rev)s'
        '</a>'
        )
        return tmpl % {
         'pref': pref,
         'cls': 'revision-link',
         'url': url('changeset_home', repo_name=repository, revision=rev),
         'rev': rev,
        }

    newtext = URL_PAT.sub(url_func, text_)

    return newtext


def urlify_commit(text_, repository=None, link_=None):
    """
    Parses given text message and makes proper links.
    issues are linked to given issue-server, and rest is a changeset link
    if link_ is given, in other case it's a plain text

    :param text_:
    :param repository:
    :param link_: changeset link
    """
    import re
    import traceback

    # urlify changesets
    text_ = urlify_changesets(text_, repository)

    def linkify_others(t, l):
        urls = re.compile(r'(\<a.*?\<\/a\>)',)
        links = []
        for e in urls.split(t):
            if not urls.match(e):
                links.append('<a class="message-link" href="%s">%s</a>' % (l, e))
            else:
                links.append(e)

        return ''.join(links)
    try:
        conf = config['app_conf']

        URL_PAT = re.compile(r'%s' % conf.get('issue_pat'))

        if URL_PAT:
            ISSUE_SERVER_LNK = conf.get('issue_server_link')
            ISSUE_PREFIX = conf.get('issue_prefix')

            def url_func(match_obj):
                pref = ''
                if match_obj.group().startswith(' '):
                    pref = ' '

                issue_id = ''.join(match_obj.groups())
                tmpl = (
                '%(pref)s<a class="%(cls)s" href="%(url)s">'
                '%(issue-prefix)s%(id-repr)s'
                '</a>'
                )
                url = ISSUE_SERVER_LNK.replace('{id}', issue_id)
                if repository:
                    url = url.replace('{repo}', repository)

                return tmpl % {
                     'pref': pref,
                     'cls': 'issue-tracker-link',
                     'url': url,
                     'id-repr': issue_id,
                     'issue-prefix': ISSUE_PREFIX,
                     'serv': ISSUE_SERVER_LNK,
                }

            newtext = URL_PAT.sub(url_func, text_)

            if link_:
                # wrap not links into final link => link_
                newtext = linkify_others(newtext, link_)

            return literal(newtext)
    except:
        log.error(traceback.format_exc())
        pass

    return text_


def rst(source):
    return literal('<div class="rst-block">%s</div>' %
                   MarkupRenderer.rst(source))


def rst_w_mentions(source):
    """
    Wrapped rst renderer with @mention highlighting

    :param source:
    """
    return literal('<div class="rst-block">%s</div>' %
                   MarkupRenderer.rst_with_mentions(source))
