__author__ = 'frublox'

import praw
import smtplib
from email.mime.text import MIMEText
import time
import ConfigParser


def read_config():
    """
    Reads config.ini and sets preferences to their according values.

    :return: None
    """

    config_parser = ConfigParser.SafeConfigParser()
    config_parser.read('config.ini')

    global user_agent, password, to_address, from_address

    user_agent = config_parser.get('bot', 'user_agent')
    to_address = config_parser.get('email', 'to_address')
    from_address = config_parser.get('email', 'from_address')
    password = config_parser.get('email', 'password')


def send_email_alert(submission_url):
    """
    Sends an email alerting of a giveaway at the specified url.

    :param submission_url: URL of the giveaway's post
    :return: None
    """
    msg = MIMEText('Giveaway happening at {}!'.format(submission_url))
    msg['Subject'] = '/r/dogecoin giveaway alert!'
    msg['From'] = from_address
    msg['To'] = to_address

    smpt_server.sendmail(from_address, [to_address], msg.as_string())

read_config()
print 'Successfully read in prefs from config.ini.'

smpt_server = smtplib.SMTP('smtp.gmail.com:587')
smpt_server.ehlo()
smpt_server.starttls()
smpt_server.login(from_address, password)
print 'Successfully connected to SMTP server!'

reddit = praw.Reddit(user_agent=user_agent)
reddit.login()
print 'Successfully connected to reddit!'

subreddit = reddit.get_subreddit('dogecoin')

already_checked = []  # for posts that have already been alerted

try:
    while True:
        for submission in subreddit.get_new(limit=10):
            if submission.id in already_checked:
                continue

            print u'Checking post "{}"...'.format(submission.title)

            if submission.title.lower().startswith('[giveaway]'):
                send_email_alert(submission.url)
                print 'Giveaway detected!'

            already_checked.append(submission.id)

        time.sleep(60)
finally:
    smpt_server.quit()