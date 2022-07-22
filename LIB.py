from datetime import date, datetime
import time
import imaplib
import email
from email.header import decode_header
import datetime
import re


def get_email_verification(username, password):
    date_stamp = datetime.datetime.now() + datetime.timedelta(minutes=239)
    # print(date_stamp)

    while True:

        body = get_email_body(username, password, 3)

        indicies = re.search(r'<br>.*GMT<br>', body)
        email_date = body[indicies.span()[0] + 4:indicies.span()[1] - 4]

        item_date = datetime.datetime.strptime(email_date, "%a, %d %b %Y %H:%M:%S GMT")
        # print(item_date)

        if (item_date > date_stamp):
            indicies = re.search(r'>\d\d\d\d\d\d<', body)

            code = body[indicies.span()[0] + 1:indicies.span()[1] - 1]

            # print(code)
            return code

        time.sleep(10)


def get_email_body(username, password, N):
    # create an IMAP4 class with SSL
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    # authenticate
    imap.login(username, password)

    status, messages = imap.select("INBOX")
    # number of top emails to fetch
    # N = 1
    # total number of emails
    messages = int(messages[0])

    for i in range(messages, messages - N, -1):
        # fetch the email message by ID
        res, msg = imap.fetch(str(i), "(RFC822)")

        for response in msg:

            if isinstance(response, tuple):
                # parse a bytes email into a message object
                msg = email.message_from_bytes(response[1])
                # decode the email subject
                subject, encoding = decode_header(msg["Subject"])[0]

                if isinstance(subject, bytes):
                    # if it's a bytes, decode to str
                    subject = subject.decode(encoding)
                # decode email sender
                From, encoding = decode_header(msg.get("From"))[0]

                if isinstance(From, bytes):
                    From = From.decode(encoding)

                # print("Subject:", subject)
                # print("From:", From)

                if "WAX Login Verification Code" in subject:

                    if msg.is_multipart():
                        # iterate over email parts

                        for part in msg.walk():
                            # extract content type of email
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            try:
                                # get the email body
                                body = part.get_payload(decode=True).decode()
                            except:
                                pass

                    else:
                        content_type = msg.get_content_type()
                        # get the email body
                        body = msg.get_payload(decode=True).decode()

                    return body
