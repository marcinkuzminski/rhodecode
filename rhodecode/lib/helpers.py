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
import re
import urlparse
import textwrap

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
from webhelpers.paginate import Page as _Page
from webhelpers.html.tags import _set_input_attrs, _set_id_attr, \
    convert_boolean_attrs, NotGiven, _make_safe_id_component

from rhodecode.lib.annotate import annotate_highlight
from rhodecode.lib.utils import repo_name_slug, get_custom_lexer
from rhodecode.lib.utils2 import str2bool, safe_unicode, safe_str, \
    get_changeset_safe, datetime_to_time, time_to_datetime, AttributeDict,\
    safe_int
from rhodecode.lib.markup_renderer import MarkupRenderer
from rhodecode.lib.vcs.exceptions import ChangesetDoesNotExistError
from rhodecode.lib.vcs.backends.base import BaseChangeset, EmptyChangeset
from rhodecode.config.conf import DATE_FORMAT, DATETIME_FORMAT
from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.db import URL_SEP, Permission

log = logging.getLogger(__name__)


html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
}


def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c, c) for c in text)


def shorter(text, size=20):
    postfix = '...'
    if len(text) > size:
        return text[:size - len(postfix)] + postfix
    return text


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

    return 'C-%s-%s' % (short_id(raw_id), md5(safe_str(path)).hexdigest()[:12])


def get_token():
    """Return the current authentication token, creating one if one doesn't
    already exist.
    """
    token_key = "_authentication_token"
    from pylons import session
    if not token_key in session:
        try:
            token = hashlib.sha1(str(random.getrandbits(128))).hexdigest()
        except AttributeError:  # Python < 2.4
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
        if form_errors and field_name in form_errors:
            return literal(tmpl % form_errors.get(field_name))

get_error = _GetError()


class _ToolTip(object):

    def __call__(self, tooltip_title, trim_at=50):
        """
        Special function just to wrap our text into nice formatted
        autowrapped text

        :param tooltip_title:
        """
        tooltip_title = escape(tooltip_title)
        tooltip_title = tooltip_title.replace('<', '&lt;').replace('>', '&gt;')
        return tooltip_title
tooltip = _ToolTip()


class _FilesBreadCrumbs(object):

    def __call__(self, repo_name, rev, paths):
        if isinstance(paths, str):
            paths = safe_unicode(paths)
        url_l = [link_to(repo_name, url('files_home',
                                        repo_name=repo_name,
                                        revision=rev, f_path=''),
                         class_='ypjax-link')]
        paths_l = paths.split('/')
        for cnt, p in enumerate(paths_l):
            if p != '':
                url_l.append(link_to(p,
                                     url('files_home',
                                         repo_name=repo_name,
                                         revision=rev,
                                         f_path='/'.join(paths_l[:cnt + 1])
                                         ),
                                     class_='ypjax-link'
                                     )
                             )

        return literal('/'.join(url_l))

files_breadcrumbs = _FilesBreadCrumbs()


class CodeHtmlFormatter(HtmlFormatter):
    """
    My code Html Formatter for source codes
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
    """
    pygmentize function using pygments

    :param filenode:
    """
    lexer = get_custom_lexer(filenode.extension) or filenode.lexer
    return literal(code_highlight(filenode.content, lexer,
                                  CodeHtmlFormatter(**kwargs)))


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
from rhodecode.lib.utils2 import credentials_filter, age as _age
from rhodecode.model.db import User, ChangesetStatus

age = lambda  x, y=False: _age(x, y)
capitalize = lambda x: x.capitalize()
email = author_email
short_id = lambda x: x[:12]
hide_credentials = lambda x: ''.join(credentials_filter(x))


def show_id(cs):
    """
    Configurable function that shows ID
    by default it's r123:fffeeefffeee

    :param cs: changeset instance
    """
    from rhodecode import CONFIG
    def_len = safe_int(CONFIG.get('show_sha_length', 12))
    show_rev = str2bool(CONFIG.get('show_revision_number', True))

    raw_id = cs.raw_id[:def_len]
    if show_rev:
        return 'r%s:%s' % (cs.revision, raw_id)
    else:
        return '%s' % (raw_id)


def fmt_date(date):
    if date:
        _fmt = _(u"%a, %d %b %Y %H:%M:%S").encode('utf8')
        return date.strftime(_fmt).decode('utf8')

    return ""


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
    # extract email from the commit string
    _email = email(author)
    if _email != '':
        # check it against RhodeCode database, and use the MAIN email for this
        # user
        user = User.get_by_email(_email, case_insensitive=True, cache=True)
        if user is not None:
            return user.email
        return _email

    # See if it contains a username we can get an email from
    user = User.get_by_username(author_name(author), case_insensitive=True,
                                cache=True)
    if user is not None:
        return user.email

    # No valid email, not a valid user in the system, none!
    return None


def person(author, show_attr="username_and_name"):
    # attr to return from fetched user
    person_getter = lambda usr: getattr(usr, show_attr)

    # Valid email in the attribute passed, see if they're in the system
    _email = email(author)
    if _email != '':
        user = User.get_by_email(_email, case_insensitive=True, cache=True)
        if user is not None:
            return person_getter(user)

    # Maybe it's a username?
    _author = author_name(author)
    user = User.get_by_username(_author, case_insensitive=True,
                                cache=True)
    if user is not None:
        return person_getter(user)

    # Still nothing?  Just pass back the author name if any, else the email
    return _author or _email


def person_by_id(id_, show_attr="username_and_name"):
    # attr to return from fetched user
    person_getter = lambda usr: getattr(usr, show_attr)

    #maybe it's an ID ?
    if str(id_).isdigit() or isinstance(id_, int):
        id_ = int(id_)
        user = User.get(id_)
        if user is not None:
            return person_getter(user)
    return id_


def desc_stylize(value):
    """
    converts tags from value into html equivalent

    :param value:
    """
    value = re.sub(r'\[see\ \=\>\ *([a-zA-Z0-9\/\=\?\&\ \:\/\.\-]*)\]',
                   '<div class="metatag" tag="see">see =&gt; \\1 </div>', value)
    value = re.sub(r'\[license\ \=\>\ *([a-zA-Z0-9\/\=\?\&\ \:\/\.\-]*)\]',
                   '<div class="metatag" tag="license"><a href="http:\/\/www.opensource.org/licenses/\\1">\\1</a></div>', value)
    value = re.sub(r'\[(requires|recommends|conflicts|base)\ \=\>\ *([a-zA-Z0-9\-\/]*)\]',
                   '<div class="metatag" tag="\\1">\\1 =&gt; <a href="/\\2">\\2</a></div>', value)
    value = re.sub(r'\[(lang|language)\ \=\>\ *([a-zA-Z\-\/\#\+]*)\]',
                   '<div class="metatag" tag="lang">\\2</div>', value)
    value = re.sub(r'\[([a-z]+)\]',
                  '<div class="metatag" tag="\\1">\\1</div>', value)

    return value


def boolicon(value):
    """Returns boolean value of a value, represented as small html image of true/false
    icons

    :param value: value
    """

    if value:
        return HTML.tag('img', src=url("/images/icons/accept.png"),
                        alt=_('True'))
    else:
        return HTML.tag('img', src=url("/images/icons/cancel.png"),
                        alt=_('False'))


def action_parser(user_log, feed=False, parse_cs=False):
    """
    This helper will action_map the specified string action into translated
    fancy names with icons and links

    :param user_log: user log instance
    :param feed: use output for feeds (no html and fancy icons)
    :param parse_cs: parse Changesets into VCS instances
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

        def lnk(rev, repo_name):
            if isinstance(rev, BaseChangeset) or isinstance(rev, AttributeDict):
                lazy_cs = True
                if getattr(rev, 'op', None) and getattr(rev, 'ref_name', None):
                    lazy_cs = False
                    lbl = '?'
                    if rev.op == 'delete_branch':
                        lbl = '%s' % _('Deleted branch: %s') % rev.ref_name
                        title = ''
                    elif rev.op == 'tag':
                        lbl = '%s' % _('Created tag: %s') % rev.ref_name
                        title = ''
                    _url = '#'

                else:
                    lbl = '%s' % (rev.short_id[:8])
                    _url = url('changeset_home', repo_name=repo_name,
                               revision=rev.raw_id)
                    title = tooltip(rev.message)
            else:
                ## changeset cannot be found/striped/removed etc.
                lbl = ('%s' % rev)[:12]
                _url = '#'
                title = _('Changeset not found')
            if parse_cs:
                return link_to(lbl, _url, title=title, class_='tooltip')
            return link_to(lbl, _url, raw_id=rev.raw_id, repo_name=repo_name,
                           class_='lazy-cs' if lazy_cs else '')

        def _get_op(rev_txt):
            _op = None
            _name = rev_txt
            if len(rev_txt.split('=>')) == 2:
                _op, _name = rev_txt.split('=>')
            return _op, _name

        revs = []
        if len(filter(lambda v: v != '', revs_ids)) > 0:
            repo = None
            for rev in revs_ids[:revs_top_limit]:
                _op, _name = _get_op(rev)

                # we want parsed changesets, or new log store format is bad
                if parse_cs:
                    try:
                        if repo is None:
                            repo = user_log.repository.scm_instance
                        _rev = repo.get_changeset(rev)
                        revs.append(_rev)
                    except ChangesetDoesNotExistError:
                        log.error('cannot find revision %s in this repo' % rev)
                        revs.append(rev)
                        continue
                else:
                    _rev = AttributeDict({
                        'short_id': rev[:12],
                        'raw_id': rev,
                        'message': '',
                        'op': _op,
                        'ref_name': _name
                    })
                    revs.append(_rev)
        cs_links = []
        cs_links.append(" " + ', '.join(
            [lnk(rev, repo_name) for rev in revs[:revs_limit]]
            )
        )
        _op1, _name1 = _get_op(revs_ids[0])
        _op2, _name2 = _get_op(revs_ids[-1])

        _rev = '%s...%s' % (_name1, _name2)

        compare_view = (
            ' <div class="compare_view tooltip" title="%s">'
            '<a href="%s">%s</a> </div>' % (
                _('Show all combined changesets %s->%s') % (
                    revs_ids[0][:12], revs_ids[-1][:12]
                ),
                url('changeset_home', repo_name=repo_name,
                    revision=_rev
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
        _url = url('summary_home', repo_name=repo_name)
        return _('fork name %s') % link_to(action_params, _url)

    def get_user_name():
        user_name = action_params
        return user_name

    def get_users_group():
        group_name = action_params
        return group_name

    def get_pull_request():
        pull_request_id = action_params
        deleted = user_log.repository is None
        if deleted:
            repo_name = user_log.repository_name
        else:
            repo_name = user_log.repository.repo_name
        return link_to(_('Pull request #%s') % pull_request_id,
                    url('pullrequest_show', repo_name=repo_name,
                    pull_request_id=pull_request_id))

    # action : translated str, callback(extractor), icon
    action_map = {
    'user_deleted_repo':           (_('[deleted] repository'),
                                    None, 'database_delete.png'),
    'user_created_repo':           (_('[created] repository'),
                                    None, 'database_add.png'),
    'user_created_fork':           (_('[created] repository as fork'),
                                    None, 'arrow_divide.png'),
    'user_forked_repo':            (_('[forked] repository'),
                                    get_fork_name, 'arrow_divide.png'),
    'user_updated_repo':           (_('[updated] repository'),
                                    None, 'database_edit.png'),
    'admin_deleted_repo':          (_('[delete] repository'),
                                    None, 'database_delete.png'),
    'admin_created_repo':          (_('[created] repository'),
                                    None, 'database_add.png'),
    'admin_forked_repo':           (_('[forked] repository'),
                                    None, 'arrow_divide.png'),
    'admin_updated_repo':          (_('[updated] repository'),
                                    None, 'database_edit.png'),
    'admin_created_user':          (_('[created] user'),
                                    get_user_name, 'user_add.png'),
    'admin_updated_user':          (_('[updated] user'),
                                    get_user_name, 'user_edit.png'),
    'admin_created_users_group':   (_('[created] user group'),
                                    get_users_group, 'group_add.png'),
    'admin_updated_users_group':   (_('[updated] user group'),
                                    get_users_group, 'group_edit.png'),
    'user_commented_revision':     (_('[commented] on revision in repository'),
                                    get_cs_links, 'comment_add.png'),
    'user_commented_pull_request': (_('[commented] on pull request for'),
                                    get_pull_request, 'comment_add.png'),
    'user_closed_pull_request':    (_('[closed] pull request for'),
                                    get_pull_request, 'tick.png'),
    'push':                        (_('[pushed] into'),
                                    get_cs_links, 'script_add.png'),
    'push_local':                  (_('[committed via RhodeCode] into repository'),
                                    get_cs_links, 'script_edit.png'),
    'push_remote':                 (_('[pulled from remote] into repository'),
                                    get_cs_links, 'connect.png'),
    'pull':                        (_('[pulled] from'),
                                    None, 'down_16.png'),
    'started_following_repo':      (_('[started following] repository'),
                                    None, 'heart_add.png'),
    'stopped_following_repo':      (_('[stopped following] repository'),
                                    None, 'heart_delete.png'),
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

    def action_parser_icon():
        action = user_log.action
        action_params = None
        x = action.split(':')

        if len(x) > 1:
            action, action_params = x

        tmpl = """<img src="%s%s" alt="%s"/>"""
        ico = action_map.get(action, ['', '', ''])[2]
        return literal(tmpl % ((url('/images/icons/')), ico, action))

    # returned callbacks we need to call to get
    return [lambda: literal(action), action_params_func, action_parser_icon]



#==============================================================================
# PERMS
#==============================================================================
from rhodecode.lib.auth import HasPermissionAny, HasPermissionAll, \
HasRepoPermissionAny, HasRepoPermissionAll, HasReposGroupPermissionAll, \
HasReposGroupPermissionAny


#==============================================================================
# GRAVATAR URL
#==============================================================================

def gravatar_url(email_address, size=30):
    from pylons import url  # doh, we need to re-import url to mock it later
    _def = 'anonymous@rhodecode.org'
    use_gravatar = str2bool(config['app_conf'].get('use_gravatar'))
    email_address = email_address or _def
    if (not use_gravatar or not email_address or email_address == _def):
        f = lambda a, l: min(l, key=lambda x: abs(x - a))
        return url("/images/user%s.png" % f(size, [14, 16, 20, 24, 30]))

    if use_gravatar and config['app_conf'].get('alternative_gravatar_url'):
        tmpl = config['app_conf'].get('alternative_gravatar_url', '')
        parsed_url = urlparse.urlparse(url.current(qualified=True))
        tmpl = tmpl.replace('{email}', email_address)\
                   .replace('{md5email}', hashlib.md5(email_address.lower()).hexdigest()) \
                   .replace('{netloc}', parsed_url.netloc)\
                   .replace('{scheme}', parsed_url.scheme)\
                   .replace('{size}', str(size))
        return tmpl

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


class Page(_Page):
    """
    Custom pager to match rendering style with YUI paginator
    """

    def _get_pos(self, cur_page, max_page, items):
        edge = (items / 2) + 1
        if (cur_page <= edge):
            radius = max(items / 2, items - cur_page)
        elif (max_page - cur_page) < edge:
            radius = (items - 1) - (max_page - cur_page)
        else:
            radius = items / 2

        left = max(1, (cur_page - (radius)))
        right = min(max_page, cur_page + (radius))
        return left, cur_page, right

    def _range(self, regexp_match):
        """
        Return range of linked pages (e.g. '1 2 [3] 4 5 6 7 8').

        Arguments:

        regexp_match
            A "re" (regular expressions) match object containing the
            radius of linked pages around the current page in
            regexp_match.group(1) as a string

        This function is supposed to be called as a callable in
        re.sub.

        """
        radius = int(regexp_match.group(1))

        # Compute the first and last page number within the radius
        # e.g. '1 .. 5 6 [7] 8 9 .. 12'
        # -> leftmost_page  = 5
        # -> rightmost_page = 9
        leftmost_page, _cur, rightmost_page = self._get_pos(self.page,
                                                            self.last_page,
                                                            (radius * 2) + 1)
        nav_items = []

        # Create a link to the first page (unless we are on the first page
        # or there would be no need to insert '..' spacers)
        if self.page != self.first_page and self.first_page < leftmost_page:
            nav_items.append(self._pagerlink(self.first_page, self.first_page))

        # Insert dots if there are pages between the first page
        # and the currently displayed page range
        if leftmost_page - self.first_page > 1:
            # Wrap in a SPAN tag if nolink_attr is set
            text = '..'
            if self.dotdot_attr:
                text = HTML.span(c=text, **self.dotdot_attr)
            nav_items.append(text)

        for thispage in xrange(leftmost_page, rightmost_page + 1):
            # Hilight the current page number and do not use a link
            if thispage == self.page:
                text = '%s' % (thispage,)
                # Wrap in a SPAN tag if nolink_attr is set
                if self.curpage_attr:
                    text = HTML.span(c=text, **self.curpage_attr)
                nav_items.append(text)
            # Otherwise create just a link to that page
            else:
                text = '%s' % (thispage,)
                nav_items.append(self._pagerlink(thispage, text))

        # Insert dots if there are pages between the displayed
        # page numbers and the end of the page range
        if self.last_page - rightmost_page > 1:
            text = '..'
            # Wrap in a SPAN tag if nolink_attr is set
            if self.dotdot_attr:
                text = HTML.span(c=text, **self.dotdot_attr)
            nav_items.append(text)

        # Create a link to the very last page (unless we are on the last
        # page or there would be no need to insert '..' spacers)
        if self.page != self.last_page and rightmost_page < self.last_page:
            nav_items.append(self._pagerlink(self.last_page, self.last_page))

        return self.separator.join(nav_items)

    def pager(self, format='~2~', page_param='page', partial_param='partial',
        show_if_single_page=False, separator=' ', onclick=None,
        symbol_first='<<', symbol_last='>>',
        symbol_previous='<', symbol_next='>',
        link_attr={'class': 'pager_link'},
        curpage_attr={'class': 'pager_curpage'},
        dotdot_attr={'class': 'pager_dotdot'}, **kwargs):

        self.curpage_attr = curpage_attr
        self.separator = separator
        self.pager_kwargs = kwargs
        self.page_param = page_param
        self.partial_param = partial_param
        self.onclick = onclick
        self.link_attr = link_attr
        self.dotdot_attr = dotdot_attr

        # Don't show navigator if there is no more than one page
        if self.page_count == 0 or (self.page_count == 1 and not show_if_single_page):
            return ''

        from string import Template
        # Replace ~...~ in token format by range of pages
        result = re.sub(r'~(\d+)~', self._range, format)

        # Interpolate '%' variables
        result = Template(result).safe_substitute({
            'first_page': self.first_page,
            'last_page': self.last_page,
            'page': self.page,
            'page_count': self.page_count,
            'items_per_page': self.items_per_page,
            'first_item': self.first_item,
            'last_item': self.last_item,
            'item_count': self.item_count,
            'link_first': self.page > self.first_page and \
                    self._pagerlink(self.first_page, symbol_first) or '',
            'link_last': self.page < self.last_page and \
                    self._pagerlink(self.last_page, symbol_last) or '',
            'link_previous': self.previous_page and \
                    self._pagerlink(self.previous_page, symbol_previous) \
                    or HTML.span(symbol_previous, class_="yui-pg-previous"),
            'link_next': self.next_page and \
                    self._pagerlink(self.next_page, symbol_next) \
                    or HTML.span(symbol_next, class_="yui-pg-next")
        })

        return literal(result)


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
    :param last_url:
    """
    groups, just_name, repo_name = groups_and_repos
    last_url = url('summary_home', repo_name=repo_name)
    last_link = link_to(just_name, last_url)

    def make_link(group):
        return link_to(group.name,
                       url('repos_group_home', group_name=group.group_name))
    return literal(' &raquo; '.join(map(make_link, groups) + ['<span>%s</span>' % last_link]))


def fancy_file_stats(stats):
    """
    Displays a fancy two colored bar for number of added/deleted
    lines of code on file

    :param stats: two element list of added/deleted lines of code
    """
    def cgen(l_type, a_v, d_v):
        mapping = {'tr': 'top-right-rounded-corner-mid',
                   'tl': 'top-left-rounded-corner-mid',
                   'br': 'bottom-right-rounded-corner-mid',
                   'bl': 'bottom-left-rounded-corner-mid'}
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

    a, d = stats[0], stats[1]
    width = 100

    if a == 'b':
        #binary mode
        b_d = '<div class="bin%s %s" style="width:100%%">%s</div>' % (d, cgen('a', a_v='', d_v=0), 'bin')
        b_a = '<div class="bin1" style="width:0%%">%s</div>' % ('bin')
        return literal('<div style="width:%spx">%s%s</div>' % (width, b_a, b_d))

    t = stats[0] + stats[1]
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

    d_a = '<div class="added %s" style="width:%s%%">%s</div>' % (
        cgen('a', a_v, d_v), a_p, a_v
    )
    d_d = '<div class="deleted %s" style="width:%s%%">%s</div>' % (
        cgen('d', a_v, d_v), d_p, d_v
    )
    return literal('<div style="width:%spx">%s%s</div>' % (width, d_a, d_d))


def urlify_text(text_, safe=True):
    """
    Extrac urls from text and make html links out of them

    :param text_:
    """

    url_pat = re.compile(r'''(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]'''
                         '''|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)''')

    def url_func(match_obj):
        url_full = match_obj.groups()[0]
        return '<a href="%(url)s">%(url)s</a>' % ({'url': url_full})
    _newtext = url_pat.sub(url_func, text_)
    if safe:
        return literal(_newtext)
    return _newtext


def urlify_changesets(text_, repository):
    """
    Extract revision ids from changeset and make link from them

    :param text_:
    :param repository: repo name to build the URL with
    """
    from pylons import url  # doh, we need to re-import url to mock it later
    URL_PAT = re.compile(r'(^|\s)([0-9a-fA-F]{12,40})($|\s)')

    def url_func(match_obj):
        rev = match_obj.groups()[1]
        pref = match_obj.groups()[0]
        suf = match_obj.groups()[2]

        tmpl = (
        '%(pref)s<a class="%(cls)s" href="%(url)s">'
        '%(rev)s</a>%(suf)s'
        )
        return tmpl % {
         'pref': pref,
         'cls': 'revision-link',
         'url': url('changeset_home', repo_name=repository, revision=rev),
         'rev': rev,
         'suf': suf
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
    import traceback
    from pylons import url  # doh, we need to re-import url to mock it later

    def escaper(string):
        return string.replace('<', '&lt;').replace('>', '&gt;')

    def linkify_others(t, l):
        urls = re.compile(r'(\<a.*?\<\/a\>)',)
        links = []
        for e in urls.split(t):
            if not urls.match(e):
                links.append('<a class="message-link" href="%s">%s</a>' % (l, e))
            else:
                links.append(e)

        return ''.join(links)

    # urlify changesets - extrac revisions and make link out of them
    newtext = urlify_changesets(escaper(text_), repository)

    # extract http/https links and make them real urls
    newtext = urlify_text(newtext, safe=False)

    try:
        from rhodecode import CONFIG
        conf = CONFIG

        # allow multiple issue servers to be used
        valid_indices = [
            x.group(1)
            for x in map(lambda x: re.match(r'issue_pat(.*)', x), conf.keys())
            if x and 'issue_server_link%s' % x.group(1) in conf
            and 'issue_prefix%s' % x.group(1) in conf
        ]

        log.debug('found issue server suffixes `%s` during valuation of: %s'
                  % (','.join(valid_indices), newtext))

        for pattern_index in valid_indices:
            ISSUE_PATTERN = conf.get('issue_pat%s' % pattern_index)
            ISSUE_SERVER_LNK = conf.get('issue_server_link%s' % pattern_index)
            ISSUE_PREFIX = conf.get('issue_prefix%s' % pattern_index)

            log.debug('pattern suffix `%s` PAT:%s SERVER_LINK:%s PREFIX:%s'
                      % (pattern_index, ISSUE_PATTERN, ISSUE_SERVER_LNK,
                         ISSUE_PREFIX))

            URL_PAT = re.compile(r'%s' % ISSUE_PATTERN)

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
                    repo_name = repository.split(URL_SEP)[-1]
                    url = url.replace('{repo_name}', repo_name)

                return tmpl % {
                     'pref': pref,
                     'cls': 'issue-tracker-link',
                     'url': url,
                     'id-repr': issue_id,
                     'issue-prefix': ISSUE_PREFIX,
                     'serv': ISSUE_SERVER_LNK,
                }
            newtext = URL_PAT.sub(url_func, newtext)
            log.debug('processed prefix:`%s` => %s' % (pattern_index, newtext))

        # if we actually did something above
        if link_:
            # wrap not links into final link => link_
            newtext = linkify_others(newtext, link_)
    except Exception:
        log.error(traceback.format_exc())
        pass

    return literal(newtext)


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


def changeset_status(repo, revision):
    return ChangesetStatusModel().get_status(repo, revision)


def changeset_status_lbl(changeset_status):
    return dict(ChangesetStatus.STATUSES).get(changeset_status)


def get_permission_name(key):
    return dict(Permission.PERMS).get(key)


def journal_filter_help():
    return _(textwrap.dedent('''
        Example filter terms:
            repository:vcs
            username:marcin
            action:*push*
            ip:127.0.0.1
            date:20120101
            date:[20120101100000 TO 20120102]

        Generate wildcards using '*' character:
            "repositroy:vcs*" - search everything starting with 'vcs'
            "repository:*vcs*" - search for repository containing 'vcs'

        Optional AND / OR operators in queries
            "repository:vcs OR repository:test"
            "username:test AND repository:test*"
    '''))


def not_mapped_error(repo_name):
    flash(_('%s repository is not mapped to db perhaps'
            ' it was created or renamed from the filesystem'
            ' please run the application again'
            ' in order to rescan repositories') % repo_name, category='error')


def ip_range(ip_addr):
    from rhodecode.model.db import UserIpMap
    s, e = UserIpMap._get_ip_range(ip_addr)
    return '%s - %s' % (s, e)
