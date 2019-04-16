# coding: utf-8

"""Class to build networkx graph objects out of MeToo twitter data."""

import os

import networkx as nx
import pandas as pd


class MeTooGraphBuilder:
    """Class to buils networkx graph objects out of MeToo twitter data."""

    def __init__(self, datadir):
        """Instantiate the object.

        datadir : path to a directory containing pre-processed data
                  from the MeToo twitter database (csv files output
                  generated using a MeTooDataExtractor instance)
        """
        # Assign and check datadir attribute.
        self.datadir = os.path.abspath(datadir)
        if not os.path.isdir(self.datadir):
            raise FileNotFoundError("No such directory: '%s'." % self.datadir)
        # List files in datadir.
        self._files = sorted(os.listdir(self.datadir))
        # Load basic users data.
        self.users = self._get_data('users.csv', index_col=0)

    def build_graphs_set(self, min_retweeted=0, keep_single=True):
        """Build networkx.DiGraph representations of the network through time.

        Select the users to consider based on the activity they generated
        by the end of the observation period. Build graphs restricted to
        those nodes based on the activity until each data collection date.
        Return a dict associating those graphs to the dates (as strings).

        min_retweeted : minimum number of retweets a user must have
                        generated by the end of the observation period
                        so as to be included in the networks
        keep_single   : whether to keep nodes that have no edges at
                        any date (i.e. people retweeting or being retweeted
                        by users not included in the dataset)
        """
        # List the available data dates.
        dates = [name[6:-4] for name in self._files if name.startswith('node')]
        dates = sorted(dates)
        # Get the last graph and select nodes based on final activity.
        last = self.build_graph(
            dates[-1], min_retweeted=min_retweeted, keep_single=keep_single
        )
        nodes = list(last.nodes)
        # Build graphs restricted to the selected nodes at each date.
        graphs = {date: self.build_graph(date, nodes) for date in dates[:-1]}
        graphs[dates[-1]] = last
        # Return the built graphs.
        return graphs

    def build_graph(
            self, date, nodes_list=None, min_retweeted=0, keep_single=True
        ):
        """Build a networkx.DiGraph of the network at a given date.

        data          : string code of the date (YYYY-MM-DD format)
                        at which to consider the network
        node_list     : optional list of nodes to restrict the network to
        min_retweeted : optional minimum number of retweets a user needs
                        to have generated so as to be included
                        (only used if `node_list` is None)
        keep_single   : whether to keep nodes with no edges
                        (only used if `node_list` is None)
        """
        # Load nodes and edges data as pandas.DataFrame.
        nodes, edges = self.load_data(
            date, nodes_list, min_retweeted, keep_single
        )
        # Create a networkx graph object and set its nodes and edges.
        graph = nx.DiGraph()
        graph.add_nodes_from(nodes.index)
        graph.add_edges_from(edges.index)
        # Add nodes attributes.
        for attr in nodes.columns[1:]:
            nx.set_node_attributes(graph, nodes[attr].to_dict(), attr)
        # Add edges attributes.
        for attr in edges.columns:
            nx.set_edge_attributes(graph, edges[attr].to_dict(), attr)
        # Return the created graph.
        return graph

    def load_data(self, date, nodes_list, min_retweeted, keep_single):
        """Return selected nodes and edges of the network at a given date.

        Load nodes and edges data at a selected date. Trim off irrelevant
        elements. Return selected data as a couple of pandas.DataFrame.

        data          : string code of the date (YYYY-MM-DD format)
                        at which to consider the network
        node_list     : optional list of nodes to restrict the network to
        min_retweeted : optional minimum number of retweets a user needs
                        to have generated so as to be included (only if
                        `node_list` is None)
        keep_single   : whether to keep nodes with no edges
                        (only used if `node_list` is None)
        """
        # Load nodes and edges information.
        nodes = self._get_data('nodes_%s.csv' % date, index_col=0)
        nodes = pd.merge(
            self.users, nodes, how='outer', left_index=True, right_index=True
        )
        edges = self._get_data('edges_%s.csv' % date)
        # Trim off nodes based on generated activity or provided listing.
        if nodes_list is None:
            nodes = nodes[nodes['n_retweeted'] >= min_retweeted]
        else:
            nodes = nodes[nodes.index.isin(nodes_list)]
        # Fill nodes' missing information with '-1' code or null values.
        nodes.iloc[:, :6] = nodes.iloc[:, :6].fillna(-1)
        nodes.iloc[:, 6:] = nodes.iloc[:, 6:].fillna(0)
        # Trim off edges that link excluded or missing nodes.
        keep = edges['dst'].isin(nodes.index) & edges['src'].isin(nodes.index)
        edges = edges.loc[keep]
        # Optionally trim further the nodes kept.
        if nodes_list is None and not keep_single:
            keep = nodes.index.isin(edges['dst'])
            keep = keep | nodes.index.isin(edges['src'])
            nodes = nodes.loc[keep]
        # Turn edges' source / destinatory columns into an index.
        edges.index = edges[['src', 'dst']].apply(tuple, axis=1)
        edges.drop(['src', 'dst'], axis=1, inplace=True)
        # Return loaded information.
        return nodes, edges

    def _get_data(self, filename, **kwargs):
        """Read and return the data from a given csv file."""
        path = os.path.join(self.datadir, filename)
        try:
            return pd.read_csv(path, **kwargs)
        except FileNotFoundError:
            if filename in self._files:
                raise KeyError("No such file in datadir: '%s'." % filename)
            raise RuntimeError(
                "File '%s' has been removed from datadir." % filename
            )
