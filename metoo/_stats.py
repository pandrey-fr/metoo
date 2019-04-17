# coding: utf-8

"""Class to compute statistics on the MeToo network through time."""


import networkx as nx
import pandas as pd


class MeTooGraphAnalyzer:
    """Class to compute statistics on the MeToo network through time."""

    def __init__(self, graphs):
        """Instantiate the object, based on pre-produced graphs.

        graphs : dict associating networkx.DiGraph instances
                 to the date of observation they correspond to;
                 see `MeTooGraphBuilder.build_graphs_set`
        """
        assert isinstance(graphs, dict)
        assert all(isinstance(value, nx.DiGraph) for value in graphs.values())
        self.graphs = graphs

    def get_metrics_set(self):
        """Compute a set of metrics on the various states of the network.

        Return three objects:
        1. A dict relative to user-wise metrics, associating to each
           metric name a couple of pandas.DataFrame, respectively
           containing statistics of the the metric at each state,
           and top ten users as to this metric, at each state.
        2. A pandas.DataFrame containing network-wide metrics
           at each state of the network.
        3. A pandas.DataFrame with summary statistics on shortest
           paths lengths at each state of the network.
        """
        # Compute summaries of user-wise statistics for each network state.
        # Also identify users with top ten highest values.
        local_metrics = (
            'average_neighbor_degree', 'clustering', 'degree',
            'degree_centrality', 'closeness_centrality', 'effective_size',
            'in_degree_centrality', 'out_degree_centrality'
        )
        local_results = {
            metric: self.synthetize(self.get_networkx_local_metric(metric))
            for metric in local_metrics
        }
        # Compute network-wide statistics for each network state.
        global_metrics = (
            'density', 'reciprocity', 'transitivity',
            'number_of_nodes', 'number_of_edges'
        )
        global_results = pd.DataFrame({
            metric: self.get_networkx_global_metric(metric)
            for metric in global_metrics
        })
        # Compute assortativity coefficients and add them to global results.
        assortativity = self.get_assortativity_coefficients()
        assortativity.columns = 'assort_' + assortativity.columns
        global_results = pd.merge(
            global_results, assortativity, left_index=True, right_index=True
        )
        # Compute statistics on shortest paths' length.
        shortest_paths = self.get_shortest_path_stats()
        # Return all sets of results.
        return local_results, global_results, shortest_paths

    def get_networkx_local_metric(self, metric):
        """Compute a user-wise network metric date-wise.

        metric : name (str) of a metric implemented as networkx.<name>

        Return a pandas.DataFrame with user-wise metrics (on rows)
        for each date (on columns).
        """
        get_metric = getattr(nx, metric)
        return pd.DataFrame({
            date: dict(get_metric(graph))
            for date, graph in self.graphs.items()
        })

    def get_networkx_global_metric(self, metric):
        """Compute a graph-wide network metric date-wise.

        metric : name (str) of a metric implemented as networkx.<name>

        Return a dict associating the graph-wide metric to each date.
        """
        get_metric = getattr(nx, metric)
        return {
            date: get_metric(graph) if graph.edges else 0
            for date, graph in self.graphs.items()
        }

    def synthetize(self, metrics):
        """Return date-wise statistics and top ten values for given metrics.

        metrics : pandas.DataFrame with user-wise metrics (on rows)
                  for each date (on columns)
        """
        # Compute date-wise summary statistics.
        stats = pd.DataFrame({
            stat: getattr(metrics, stat)(axis=0)
            for stat in ('mean', 'std', 'median')
        }).round(3)
        # Identify top ten users (and associated values).
        top = metrics.apply(self._get_top_ten, axis=0)
        # Return both pandas.DataFrame objects.
        return stats, top

    @staticmethod
    def _get_top_ten(series):
        """Return top-ten values (and index) in a pandas.Series.

        Return a pandas.Series containing (index, value) tuples
        ordered from first to tenth highest value in `series`.
        """
        top = series.sort_values(ascending=False)[:10]
        return pd.Series(list(top.items()))

    def get_assortativity_coefficients(self):
        """Compute degree and attribute assortativity coefficients."""
        attributes = (
            'followers_count', 'n_tweets', 'n_retweeted',
            'sentiment_avg', 'sentiment_abs_avg'
        )
        # Compute attribute-wise assortativity coefficients, date-wise.
        coefficients = pd.DataFrame({
            date: {
                attr: nx.attribute_assortativity_coefficient(graph, attr)
                for attr in attributes
            }
            for date, graph in self.graphs.items()
        })
        # Add degree assortativity coefficients to the results. Return them.
        coefficients.loc['degree'] = (
            self.get_networkx_global_metric('degree_assortativity_coefficient')
        )
        return coefficients.T

    def get_shortest_path_stats(self):
        """Return summary statistics on shortest paths within each graph."""
        return pd.DataFrame({
            date: self._get_shortest_path_stats(graph)
            for date, graph in self.graphs.items()
        })

    @staticmethod
    def _get_shortest_path_stats(graph):
        """Return summary statistics on shortest paths within a given graph."""
        # shortest paths (for a given graph)
        path_lengths = pd.Series([
            length for _, paths in nx.shortest_path_length(graph)
            for length in paths.values() if length
        ])
        return path_lengths.describe().T
