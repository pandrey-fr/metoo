# coding: utf-8

"""Extract and reformat  data from the MeToo Twitter database."""

from operator import itemgetter
import os

import pandas as pd

from metoo import MeTooDataLoader


class MeTooDataExtractor:
    """Class to extract and reformat data from the MeToo Twitter database."""

    def __init__(self, dbpath):
        """Instantiate the object and load the data from SQLite."""
        self.dbpath = os.path.abspath(dbpath)
        self.tweets = None
        self.users = None
        self.load_data()

    def load_data(self):
        """Reload the tweets and users data from the SQLite database."""
        loader = MeTooDataLoader(self.dbpath)
        self.tweets = loader.tweets
        self.users = loader.users

    def extract_data(self, datadir, hashtags=None, mentions=None):
        """Extract and record to csv network data for each date.

        For each date in the initial dataset, write a couple
        of csv files recording information on nodes (users)
        and edges (retweets) based on activity up to that
        date. Additionnally, record copies of the initial
        tweets and users tables.

        datadir  : directory in which to record the csv files
        hashtags : optional list of hashtags to record information about
        mentions : optional list of mentions to record information about
        """
        # Create output directory if needed.
        datadir = os.path.abspath(datadir)
        if not os.path.isdir(datadir):
            os.makedirs(datadir)
        # Get tweets data on the entire time period.
        tweets = self.get_tweets_data(hashtags, mentions)
        # Declare a container for overall statitics.
        stats = {}
        # Iterate over the unique dates in the period.
        for date in sorted(tweets['created'].unique()):
            # Trim off tweets ulterior to the current date.
            subtweets = tweets[tweets['created'] <= date]
            # Compute global statitics at that date.
            stats[str(date)] = self.get_tweets_stats(subtweets)
            # Extract nodes and edges data at that date.
            path = os.path.join(datadir, '{0}_%s.csv' % date)
            self.__extract_data(subtweets, path)
            print('Done with date %s.' % date)
        # Turn date-wise global stats into a pandas.DataFrame.
        stats = pd.DataFrame(stats).T
        for col in stats.columns:
            if col[0] == 'n':
                stats[col] = stats[col].astype(int)
        # Record global information to csv.
        path = os.path.join(datadir, '{0}.csv')
        stats.to_csv(path.format('stats'), index_label='date')
        self.tweets.to_csv(path.format('tweets'), index=False)
        self.users.to_csv(path.format('users'), index_label='user')
        print('Done extracting all information to csv files.')

    def __extract_data(self, tweets, path):
        """Extract and export nodes and edges data from a given subselection.

        tweets : subselection of tweets based on which to compute
                 nodes' and edges' attributes
        path   : pre-built string pointing to output csv files,
                 comprising a single {{0}} field to format out
        """
        # Compute user-wise (nodes) statistics.
        nodes = self.get_tweets_stats(tweets, groupby='screenName')
        # Subselect retweets and tag them by tweeter-retweeter couple.
        retweets = tweets[tweets['is_retweet']].copy()
        retweets['edge'] = retweets['screenName'] + ' ' + retweets['retweet']
        # Compute edge-wise statistics.
        edges = self.get_tweets_stats(retweets, groupby='edge')
        edges.drop(['n_tweets', 'n_replies', 'n_retweeted'], 1, inplace=True)
        # Process edges' index to record edge identity information.
        edges.index = edges.index.str.split(' ')
        edges['src'] = edges.index.map(itemgetter(0))
        edges['dst'] = edges.index.map(itemgetter(1))
        # Record both processed datasets to csv.
        nodes.to_csv(path.format('nodes'), index_label='user')
        edges.to_csv(path.format('edges'), index=False)

    def get_tweets_data(self, hashtags=None, mentions=None):
        """Return a reformatted copy of the tweets database.

        Replace all complex information with dummies, easing
        the computation of derived statistics.

        hashtags : optional list of hashtags to create dummy columns about
        mentions : optional list of mentions to create dummy columns about
        """
        # Select information to keep as such, and parse creation times.
        tweets = self.tweets.copy()
        tweets['created'] = pd.to_datetime(tweets['created']).dt.date
        # Create dummies based on more complex information.
        tweets['is_reply'] = tweets['reply'].notnull()
        tweets['is_retweet'] = tweets['retweet'].notnull()
        tweets.loc[tweets['is_retweet'], 'retweetCount'] = 0
        tweets['sentiment_abs'] = tweets['sentiment_score'].abs()
        tweets['sentiment_pos'] = (tweets['sentiment_score'] > 0).astype(int)
        tweets['sentiment_neg'] = (tweets['sentiment_score'] < 0).astype(int)
        # Optionally create dummies based on hashtags and mentions.
        triplets = (('hashtags', '#', hashtags), ('mentions', '@', mentions))
        for name, symbol, tags in triplets:
            if not isinstance(tags, list):
                continue
            for tag in tags:
                # irrelevant warning; pylint: disable=cell-var-from-loop
                tweets[symbol + tag] = (
                    tweets[name].apply(lambda x: tag in x).astype(int)
                )
        # Return the extracted scores and dummies.
        return tweets

    @staticmethod
    def get_tweets_stats(tweets, groupby=None):
        """Compute statistics based on a pandas.DataFrame of tweets.

        tweets  : pandas.DataFrame containing tweets data
        groupby : optional tweets column name to group tweets
                  by unique values and compute group-wise stats

        Return a dict of statistics if `groupby` is None, and
        a pandas.DataFrame with similar statistics computed for
        each unique value in the groupby column otherwise.
        """
        # Set up the dataset to work on, with optional grouping.
        tags = [name for name in tweets.columns if name[0] in '@#']
        if groupby is not None:
            tweets = tweets.groupby(groupby)
        # Compute default statistics.
        results = {
            'n_tweets': tweets.apply(len) if groupby else len(tweets),
            'n_replies': tweets['is_reply'].sum().astype(int),
            'n_retweets': tweets['is_retweet'].sum().astype(int),
            'n_retweeted': tweets['retweetCount'].sum().astype(int),
            'sentiment_avg': round(tweets['sentiment_score'].mean(), 2),
            'sentiment_abs_avg': round(tweets['sentiment_abs'].mean(), 2),
            'share_positive': round(tweets['sentiment_pos'].mean(), 2),
            'share_negative': round(tweets['sentiment_neg'].mean(), 2)
        }
        # Compute additionnal statitics on hashtags and mentions.
        results.update({
            'n_' + tag: tweets[tag].sum().astype(int) for tag in tags
        })
        # Return results.
        return results if groupby is None else pd.DataFrame(results)
