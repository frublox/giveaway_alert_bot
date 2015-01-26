__author__ = 'frublox'

import praw
from praw.errors import InvalidUserPass

import smtplib
from smtplib import SMTPException
from smtplib import SMTPAuthenticationError
from smtplib import SMTPHeloError
from smtplib import SMTPConnectError

from email.mime.text import MIMEText

import configparser
import time
import datetime
import sys


def log(message):
    """
    Logs a message based on the log_level field in config.ini.

    Log level meanings:
    0 - Only print message o console
    1 - Print message to console and append it to the log file specified in config.ini

    :param message: The message to log
    :return: None
    """

    print(message)

    def log_to_file():
        with open(prefs['log_file'], 'a') as log_file:
            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            log_file.write(timestamp + ': ' + message + '\n')

    options = {
        1: log_to_file
    }

    if options.get(prefs['log_level']) is not None:
        options[prefs['log_level']]()
    else:
        print("Error: Invalid log level setting. Check the config.ini file.")


def get_prefs():
    """
    Reads prefs from config.ini into a dictionary.

    :return: Dictionary of prefs
    """
    config_parser = configparser.ConfigParser()
    config_parser.read('config.ini')

    prefs_dict = {
        'user_agent': config_parser.get('bot', 'user_agent'),
        'sleep_time': config_parser.getint('bot', 'sleep_time'),
        'log_level': config_parser.getint('bot', 'log_level'),
        'log_file': config_parser.get('bot', 'log_file'),
        'to_address': config_parser.get('email', 'to_address'),
        'from_address': config_parser.get('email', 'from_address'),
        'password': config_parser.get('email', 'password')
    }

    log('Successfully read in prefs from config.ini.')

    return prefs_dict


def send_email_alert(smtp_server, submission_url):
    """
    Sends an email alerting of a giveaway at the specified url.

    :param submission_url: URL of the giveaway's post
    :return: None
    """
    msg = MIMEText('Giveaway happening at {}!'.format(submission_url))
    msg['Subject'] = '/r/dogecoin giveaway alert!'
    msg['From'] = prefs['from_address']
    msg['To'] = prefs['to_address']

    try:
        smtp_server.sendmail(prefs['from_address'], [prefs['to_address']], msg.as_string())
        log('Sent email alert.')
    except IOError as e:
        log('Failed to send email alert. Error: {}'.format(e))


def get_reddit_instance():
    """
    Creates a PRAW reddit instance, logs in, and then returns that instance.
    Will exit the program if an error occurs.

    :return: A logged-in PRAW reddit instance.
    """
    reddit = praw.Reddit(user_agent=prefs['user_agent'])

    try:
        reddit.login()
    except InvalidUserPass:
        log('Error: the login credentials specified in praw.ini are incorrect.')
        log('Exiting...')
        sys.exit(1)

    log('Successfully logged into reddit!')

    return reddit


def get_smtp_connection():
    """
    Connects to the gmail SMTP server and logs in, returning an SMTP connection instance.
    Will exit the program if an error occurs.

    :return: A logged-in SMTP connection instance
    """
    smtp_connection = smtplib.SMTP('smtp.gmail.com', 587)

    # default behaviour in case the next try block catches an exception
    def handle_error():
        log('Exiting...')
        smtp_connection.quit()
        sys.exit(1)

    try:
        # use this line to see what's going on with the SMTP connection
        # smtp_server_connection.set_debuglevel(1)
        smtp_connection.ehlo()
        smtp_connection.starttls()
        smtp_connection.login(prefs['from_address'], prefs['password'])
    except SMTPAuthenticationError:
        log('Error: SMTP server refused to authenticate connection -- perhaps login credentials are incorrect?')
        handle_error()
    except SMTPHeloError:
        log('Error: SMTP server responded improperly to HELO greeting.')
        handle_error()
    except SMTPConnectError:
        log('Error: Failed to connect to SMTPServer.')
        handle_error()
    except SMTPException as e:
        log('Error: An SMTPException occurred: {}'.format(e))
        handle_error()

    log('Successfully connected and logged in to SMTP server!')

    return smtp_connection


def check_posts(reddit, smtp_connection):
    """
    Checks new posts in /r/dogecoin for a giveaway, and sends an email if one is found.

    :return: None
    """
    subreddit = reddit.get_subreddit('dogecoin')

    already_checked = []

    while True:
        for submission in subreddit.get_new(limit=30):
            if submission.id in already_checked:
                continue

            if submission.link_flair_text is not None:
                if submission.link_flair_text.lower() == "giveaway":
                    log('Giveaway detected at: {}'.format(submission.url))
                    send_email_alert(smtp_connection, submission.url)

            already_checked.append(submission.id)

        time.sleep(prefs['sleep_time'])


def main():
    smtp_connection = None

    try:
        while True:
            smtp_connection = get_smtp_connection()
            reddit = get_reddit_instance()
            check_posts(reddit, smtp_connection)
    except IOError as e:
        log('Error: {}'.format(e))
        log('Attempting to reconnect...')
        main()
    finally:
        if smtp_connection is not None:
            smtp_connection.quit()


if __name__ == '__main__':
    global prefs
    prefs = get_prefs()
    main()