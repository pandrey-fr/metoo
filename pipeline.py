# coding: utf-8

"""Results production pipeline - meant to be called as a script."""

import os
import pickle

import networkx as nx

import metoo


DBPATH = '~/Bureau/metoo/workdir/MeToo.sqlite'
WORKDIR = '~/Bureau/metoo/workdir'
DATADIR = os.path.join(WORKDIR, 'data')


def main():
    """Run a results-production pipeline and dump results to a pickle file."""
    # Extract data from MeToo.sqlite to the data directory.
    extractor = metoo.MeTooDataExtractor(DBPATH)
    extractor.extract_data(DATADIR)
    del extractor
    # Build graphs for a subpopulation, at each date.
    builder = metoo.MeTooGraphBuilder(DATADIR)
    graphs = builder.build_graphs_set(min_retweeted=10, keep_single=False)
    subgrp = builder.build_graphs_set(min_retweeted=10, connected=True)
    del builder
    print('Done building the (sub)graphs sets.')
    # Export final graph state for visual exploitation with Gephi.
    nx.write_gexf(graphs['2017-12-25'], os.path.join(WORKDIR, 'graph.gexf'))
    nx.write_gexf(subgrp['2017-12-25'], os.path.join(WORKDIR, 'subgraph.gexf'))
    # Draw and save plots of the graphs. Make videos if opencv is available.
    drawer = metoo.MeTooGraphDrawer()
    args = ('sentiment_avg', 'n_retweets', 'sentiment_avg')
    for node_size in ('followers_count', 'n_retweeted'):
        path = os.path.join(WORKDIR, 'plots_' + node_size)
        drawer.draw_graphs_set(graphs, path, True, node_size, *args)
    del drawer
    print('Done drawing graphs through time.')
    # Compute network statistics based on the (sub)graphs.
    stats_graphs = metoo.MeTooGraphAnalyzer(graphs).get_metrics_set()
    stats_subgrp = metoo.MeTooGraphAnalyzer(subgrp).get_metrics_set()
    print('Done computing graphs metrics.')
    # Dump to pickle files the graphs and statistics produced.
    results = {
        'graphs': graphs, 'stats_graphs': stats_graphs,
        'subgraphs': subgrp, 'stats_subgraphs': stats_subgrp
    }
    with open(os.path.join(WORKDIR, 'results.pickle')) as file:
        pickle.dump(results, file)
    print('Done producing results and dumping them to a pickle file.')


if __name__ == '__main__':
    main()
