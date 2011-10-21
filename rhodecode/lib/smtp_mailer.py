# -*- coding: utf-8 -*-
"""
    rhodecode.lib.smtp_mailer
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Simple smtp mailer used in RhodeCode

    :created_on: Sep 13, 2010
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>
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

import logging
import smtplib
import mimetypes
from socket import sslerror

from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders


class SmtpMailer(object):
    """SMTP mailer class

    mailer = SmtpMailer(mail_from, user, passwd, mail_server, smtp_auth
                        mail_port, ssl, tls)
    mailer.send(recipients, subject, body, attachment_files)

    :param recipients might be a list of string or single string
    :param attachment_files is a dict of {filename:location}
        it tries to guess the mimetype and attach the file

    """

    def __init__(self, mail_from, user, passwd, mail_server, smtp_auth=None,
                 mail_port=None, ssl=False, tls=False, debug=False):

        self.mail_from = mail_from
        self.mail_server = mail_server
        self.mail_port = mail_port
        self.user = user
        self.passwd = passwd
        self.ssl = ssl
        self.tls = tls
        self.debug = debug
        self.auth = smtp_auth

    def send(self, recipients=[], subject='', body='', attachment_files=None):

        if isinstance(recipients, basestring):
            recipients = [recipients]
        if self.ssl:
            smtp_serv = smtplib.SMTP_SSL(self.mail_server, self.mail_port)
        else:
            smtp_serv = smtplib.SMTP(self.mail_server, self.mail_port)

        if self.tls:
            smtp_serv.ehlo()
            smtp_serv.starttls()

        if self.debug:
            smtp_serv.set_debuglevel(1)

        smtp_serv.ehlo()
        if self.auth:
            smtp_serv.esmtp_features["auth"] = self.auth

        # if server requires authorization you must provide login and password
        # but only if we have them
        if self.user and self.passwd:
            smtp_serv.login(self.user, self.passwd)

        date_ = formatdate(localtime=True)
        msg = MIMEMultipart()
        msg.set_type('multipart/alternative')
        msg.preamble = 'You will not see this in a MIME-aware mail reader.\n'

        text_msg = MIMEText(body)
        text_msg.set_type('text/plain')
        text_msg.set_param('charset', 'UTF-8')

        msg['From'] = self.mail_from
        msg['To'] = ','.join(recipients)
        msg['Date'] = date_
        msg['Subject'] = subject

        msg.attach(text_msg)

        if attachment_files:
            self.__atach_files(msg, attachment_files)

        smtp_serv.sendmail(self.mail_from, recipients, msg.as_string())
        logging.info('MAIL SEND TO: %s' % recipients)

        try:
            smtp_serv.quit()
        except sslerror:
            # sslerror is raised in tls connections on closing sometimes
            pass

    def __atach_files(self, msg, attachment_files):
        if isinstance(attachment_files, dict):
            for f_name, msg_file in attachment_files.items():
                ctype, encoding = mimetypes.guess_type(f_name)
                logging.info("guessing file %s type based on %s", ctype,
                             f_name)
                if ctype is None or encoding is not None:
                    # No guess could be made, or the file is encoded
                    # (compressed), so use a generic bag-of-bits type.
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                if maintype == 'text':
                    # Note: we should handle calculating the charset
                    file_part = MIMEText(self.get_content(msg_file),
                                         _subtype=subtype)
                elif maintype == 'image':
                    file_part = MIMEImage(self.get_content(msg_file),
                                          _subtype=subtype)
                elif maintype == 'audio':
                    file_part = MIMEAudio(self.get_content(msg_file),
                                          _subtype=subtype)
                else:
                    file_part = MIMEBase(maintype, subtype)
                    file_part.set_payload(self.get_content(msg_file))
                    # Encode the payload using Base64
                    encoders.encode_base64(msg)
                # Set the filename parameter
                file_part.add_header('Content-Disposition', 'attachment',
                                     filename=f_name)
                file_part.add_header('Content-Type', ctype, name=f_name)
                msg.attach(file_part)
        else:
            raise Exception('Attachment files should be'
                            'a dict in format {"filename":"filepath"}')

    def get_content(self, msg_file):
        """Get content based on type, if content is a string do open first
        else just read because it's a probably open file object

        :param msg_file:
        """
        if isinstance(msg_file, str):
            return open(msg_file, "rb").read()
        else:
            # just for safe seek to 0
            msg_file.seek(0)
            return msg_file.read()

