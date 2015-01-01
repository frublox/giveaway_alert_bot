giveaway_alert_bot
==================

Note: this was made with Python 2.7. If you want to update for Python 3 and aboe, just make the print statements into functions and change 'import ConfigParser' to 'import configparser'.

reddit bot that looks for giveaway posts on /r/dogecoin.

Simply searches through new posts on /r/dogecoin and check if the post's title starts with a [Giveaway] tag. If it does, the bot sends an email to the address specified in the config.ini file. Uses a local praw.ini to log in to reddit.
