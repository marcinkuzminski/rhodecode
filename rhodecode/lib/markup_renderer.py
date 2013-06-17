# -*- coding: utf-8 -*-
"""
    rhodecode.lib.markup_renderer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


    Renderer for markup languages with ability to parse using rst or markdown

    :created_on: Oct 27, 2011
    :author: marcink
    :copyright: (C) 2011-2012 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import logging
import traceback

from rhodecode.lib.utils2 import safe_unicode, MENTIONS_REGEX

log = logging.getLogger(__name__)


class MarkupRenderer(object):
    RESTRUCTUREDTEXT_DISALLOWED_DIRECTIVES = ['include', 'meta', 'raw']

    MARKDOWN_PAT = re.compile(r'md|mkdn?|mdown|markdown', re.IGNORECASE)
    RST_PAT = re.compile(r're?st', re.IGNORECASE)
    PLAIN_PAT = re.compile(r'readme', re.IGNORECASE)

    def _detect_renderer(self, source, filename=None):
        """
        runs detection of what renderer should be used for generating html
        from a markup language

        filename can be also explicitly a renderer name

        :param source:
        :param filename:
        """

        if MarkupRenderer.MARKDOWN_PAT.findall(filename):
            detected_renderer = 'markdown'
        elif MarkupRenderer.RST_PAT.findall(filename):
            detected_renderer = 'rst'
        elif MarkupRenderer.PLAIN_PAT.findall(filename):
            detected_renderer = 'rst'
        else:
            detected_renderer = 'plain'

        return getattr(MarkupRenderer, detected_renderer)

    @classmethod
    def _flavored_markdown(cls, text):
        """
        Github style flavored markdown

        :param text:
        """
        from hashlib import md5

        # Extract pre blocks.
        extractions = {}
        def pre_extraction_callback(matchobj):
            digest = md5(matchobj.group(0)).hexdigest()
            extractions[digest] = matchobj.group(0)
            return "{gfm-extraction-%s}" % digest
        pattern = re.compile(r'<pre>.*?</pre>', re.MULTILINE | re.DOTALL)
        text = re.sub(pattern, pre_extraction_callback, text)

        # Prevent foo_bar_baz from ending up with an italic word in the middle.
        def italic_callback(matchobj):
            s = matchobj.group(0)
            if list(s).count('_') >= 2:
                return s.replace('_', '\_')
            return s
        text = re.sub(r'^(?! {4}|\t)\w+_\w+_\w[\w_]*', italic_callback, text)

        # In very clear cases, let newlines become <br /> tags.
        def newline_callback(matchobj):
            if len(matchobj.group(1)) == 1:
                return matchobj.group(0).rstrip() + '  \n'
            else:
                return matchobj.group(0)
        pattern = re.compile(r'^[\w\<][^\n]*(\n+)', re.MULTILINE)
        text = re.sub(pattern, newline_callback, text)

        # Insert pre block extractions.
        def pre_insert_callback(matchobj):
            return '\n\n' + extractions[matchobj.group(1)]
        text = re.sub(r'{gfm-extraction-([0-9a-f]{32})\}',
                      pre_insert_callback, text)

        return text

    def render(self, source, filename=None):
        """
        Renders a given filename using detected renderer
        it detects renderers based on file extension or mimetype.
        At last it will just do a simple html replacing new lines with <br/>

        :param file_name:
        :param source:
        """

        renderer = self._detect_renderer(source, filename)
        readme_data = renderer(source)
        return readme_data

    @classmethod
    def plain(cls, source):
        source = safe_unicode(source)

        def urlify_text(text):
            url_pat = re.compile(r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]'
                                 '|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)')

            def url_func(match_obj):
                url_full = match_obj.groups()[0]
                return '<a href="%(url)s">%(url)s</a>' % ({'url': url_full})

            return url_pat.sub(url_func, text)

        source = urlify_text(source)
        return '<br />' + source.replace("\n", '<br />')

    @classmethod
    def markdown(cls, source, safe=True, flavored=False):
        source = safe_unicode(source)
        try:
            import markdown as __markdown
            if flavored:
                source = cls._flavored_markdown(source)
            return __markdown.markdown(source, ['codehilite', 'extra'])
        except ImportError:
            log.warning('Install markdown to use this function')
            return cls.plain(source)
        except Exception:
            log.error(traceback.format_exc())
            if safe:
                return source
            else:
                raise

    @classmethod
    def rst(cls, source, safe=True):
        source = safe_unicode(source)
        try:
            from docutils.core import publish_parts
            from docutils.parsers.rst import directives
            docutils_settings = dict([(alias, None) for alias in
                                cls.RESTRUCTUREDTEXT_DISALLOWED_DIRECTIVES])

            docutils_settings.update({'input_encoding': 'unicode',
                                      'report_level': 4})

            for k, v in docutils_settings.iteritems():
                directives.register_directive(k, v)

            parts = publish_parts(source=source,
                                  writer_name="html4css1",
                                  settings_overrides=docutils_settings)

            return parts['html_title'] + parts["fragment"]
        except ImportError:
            log.warning('Install docutils to use this function')
            return cls.plain(source)
        except Exception:
            log.error(traceback.format_exc())
            if safe:
                return source
            else:
                raise

    @classmethod
    def rst_with_mentions(cls, source):
        mention_pat = re.compile(MENTIONS_REGEX)

        def wrapp(match_obj):
            uname = match_obj.groups()[0]
            return ' **@%(uname)s** ' % {'uname': uname}
        mention_hl = mention_pat.sub(wrapp, source).strip()
        return cls.rst(mention_hl)
