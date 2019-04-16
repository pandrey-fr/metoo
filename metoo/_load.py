# coding: utf-8

"""Import and parse data from the MeToo Twitter database."""

import os
import re
import sqlite3

import pandas as pd


class MeTooDataLoader:
    """Class to import and pre-process the MeToo tweets SQLite database."""
    # No need for more methods; pylint: disable=too-few-public-methods

    def __init__(self, dbpath):
        """Instantiate the object by importing and parsing the database."""
        # Check dbpath argument validity and assign it as attribute.
        dbpath = os.path.abspath(dbpath)
        if not os.path.isfile(dbpath):
            raise FileNotFoundError("No such file: '%s'." % dbpath)
        if not dbpath.endswith('.sqlite'):
            raise ValueError("'dbpath' should point to a .sqlite file.")
        self.dbpath = dbpath
        # Declare empty attributes and fill them by loading the database.
        self.tweets = None
        self.users = None
        self.load()

    def load(self):
        """Load or reload the MeToo tweets and users data from SQLite.

        Read information from the initial tweets and users tables,
        then parse tweets' text for additionnal information.
        """
        # Import the users and tweets tables from the SQLite database.
        with sqlite3.connect(self.dbpath) as connection:
            cursor = connection.cursor()
            self.tweets = self.__import_tweets(cursor)
            self.users = self.__import_users(cursor)
        # Parse tweets and enrich the imported dataset with identified info.
        self.__parse_tweets()

    @staticmethod
    def _dataframe_from_sqlite(query, cursor):
        """Import a SQLite table as a pandas.DataFrame.

        query  : sqlite query to select the imported data
        cursor : sqlite3.cursor object to the sqlite database
        """
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall())
        data.columns = [info[0] for info in cursor.description]
        return data

    def __import_users(self, cursor):
        """Import and return the users table."""
        # Import selected columns from the tweets table.
        query = 'SELECT screenName, created_at, verified, followers_count, '
        query += 'friends_count, favourites_count, statuses_count FROM users'
        users = self._dataframe_from_sqlite(query, cursor)
        users.index = users['screenName']
        return users.drop('screenName', axis=1)

    def __import_tweets(self, cursor):
        """Import and return the tweets table."""
        query = 'SELECT screenName, sentiment_score, created, retweetCount, '
        query += 'favoriteCount, text, replyToSN FROM tweets'
        tweets = self._dataframe_from_sqlite(query, cursor)
        tweets.columns = list(tweets.columns[:-1]) + ['reply']
        return tweets

    def __parse_tweets(self):
        """Look up retweets, mentions and hashtags within tweets.

        Enrich and return a tweets dataframe by searching its 'text' column.
        """
        # Compile and use regular expressions to look up information.
        regular_expressions = (
            ('retweet', re.compile('^RT @(\\w+):')),
            ('mentions', re.compile('@(\\w+)')),
            ('hashtags', re.compile('#(\\w+)'))
        )
        for name, regex in regular_expressions:
            self.tweets[name] = self.tweets['text'].apply(regex.findall)
        # Put hashtags to lower case to reduce ambiguities.
        self.tweets['hashtags'] = self.tweets['hashtags'].apply(
            lambda x: [e.lower() for e in x]
        )
        # Change the format of the retweet column.
        self.tweets['retweet'] = self.tweets['retweet'].apply(
            lambda x: x[0] if x else None
        )
        # Drop the texts, now that they have been parsed.
        self.tweets.drop('text', axis=1, inplace=True)
