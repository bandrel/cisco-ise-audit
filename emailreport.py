#!/usr/bin/env python
__author__ = 'Justin Bollinger'

import ConfigParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, timedelta
import time
import smtplib
import os
from email import Encoders

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText



yesterday = date.today() - timedelta(1)
def EmailHTML(messagelist,zfile):
    config = ConfigParser.ConfigParser()
    config.read('config.ini')
    email_server = config.get("Email", "host")
    subject = config.get("Email", "subject")
    fromaddress = config.get("Email", "from_address")
    ta = config.get("Email", "to_address")
    toaddress = ta.split()
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['To'] = ", ".join(toaddress)
    msg['From'] = fromaddress
    fileattach = config.get("Email", "attachment").upper()
    txtmessage = ''
    for line in messagelist:
        tl = line.split(',')
        txtmessage = txtmessage + '<tr><td>' + str(tl[0]) + '</td><td>' +  str(tl[1]) + '</td><td>'\
        +  str(tl[2]) + '</tr></td>'
    if messagelist == []:
        html = """\
        <html>
          <head></head>
          <body>
          <H3>There were no interface changes between """ + yesterday.strftime('%m-%d-%Y') + ' and ' + time.strftime('%m-%d-%Y') + """
          </H3>
            </body>
        </html>
        """
    else:
        html = """\
        <html>
          <head></head>
          <body>
          <H3>Interfaces changed between """ + yesterday.strftime('%m-%d-%Y') + ' and ' + time.strftime('%m-%d-%Y') + \
          '</H3><table cellpadding="10">' + txtmessage + """\
            </table>
            </body>
        </html>
        """

    if fileattach == 'YES':
        f = str(zfile)
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(html, 'html')
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)

    # Send the message via local SMTP server.
    s = smtplib.SMTP(email_server)
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    s.sendmail(fromaddress, toaddress, msg.as_string())
    return
