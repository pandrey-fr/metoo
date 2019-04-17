# coding: utf-8

"""Class to draw MeToo twitter graphs."""

import os
import warnings

try:
    import cv2
    VIDEO_FEATURES = True
except ModuleNotFoundError:
    VIDEO_FEATURES = False
import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd


class MeTooGraphDrawer:
    """Class to draw MeToo twitter graphs."""

    def __init__(
            self, figsize=(18, 10), node_size_limits=(5, 100),
            edge_size_limits=(1, 10)
        ):
        """Instantiate the object, setting up some display parameters."""
        # Check arguments' validity.
        for argument in (figsize, node_size_limits, edge_size_limits):
            assert isinstance(argument, tuple) and len(argument) == 2
            assert all(isinstance(value, int) for value in argument)
        # Assign attributes.
        self.figsize = figsize
        self.node_size_limits = node_size_limits
        self.edge_size_limits = edge_size_limits

    def draw_graphs_set(
            self, graphs, imagedir, video=True, layout='fruchterman_reingold',
            node_size=None, node_color=None, edge_size=None, edge_color=None,
            node_labels=False, **kwargs
        ):
        """Draw and save successive representations of a network.

        This function is meant to be passed the dict resulting from
        calling the `MeTooGraphBuilder.build_graphs_set` method.

        graphs   : dict containing various states of the MeToo graph,
                   indexed by the date they correspond to
        imagedir : directory where to output drawn figures
        video    : whether to make an mp4 video rendering based
                   on the produced images (bool, default True)
                   (only valid if cv2 module is installed)
        layout   : name (str) of the networkx layout to use
                   (default 'fruchterman_reingold')

        Remaining arguments are those of `MeTooGraphDrawer.draw_graph`.
        See documentation of the former for details.
        """
        # arguments serve modularity; pylint: disable=too-many-arguments
        # variables serve readability; pylint: disable=too-many-locals
        # Set up the output directory if needed.
        imagedir = os.path.abspath(imagedir)
        if not os.path.isdir(imagedir):
            os.makedirs(imagedir)
        # Compute nodes position once and for all based on final state.
        layout = getattr(nx, layout + '_layout')
        positions = layout(graphs[list(graphs)[-1]])
        # Iteratively draw and save figures of the graph at each date.
        for date, graph in graphs.items():
            figure = self.draw_graph(
                graph, node_size, node_color, edge_size, edge_color,
                positions, node_labels, **kwargs
            )
            plt.title(date)
            figure.savefig(os.path.join(imagedir, 'network_%s.png' % date))
            plt.close(figure)
        # Optionally make a video rendering out of the produced images.
        if video and VIDEO_FEATURES:
            self.make_video(os.path.join(imagedir, 'video.mp4'), imagedir)

    def draw_graph(
            self, graph, node_size=None, node_color=None, edge_size=None,
            edge_color=None, positions=None, node_labels=False, **kwargs
        ):
        """Draw a given MeToo tweeter graph.

        Use modular arguments to adjust nodes and edges' display properties.

        graph       : networkx.DiGraph object to plot
        node_size   : opt. attribute to set nodes' size based on which
        node_color  : opt. attribute to set nodes' color based on which
        edge_size   : opt. attribute to set edges' size based on which
        edge_color  : opt. attribute to set edges' color based on which
        positions   : optional pre-computed nodes' positions
        node_labels : whether to display node labels (bool, default False)

        Additionnally, you may specify the use of logarithm to scale
        values used to set up nodes and edges' sizes and colors, by
        passing `log_<element>_<type>=True` keyword arguments, with
        <element> in {{'node', 'edge'}} and <type> in {{'size', 'color'}}.
        """
        # arguments serve modularity; pylint: disable=too-many-arguments
        figure = plt.figure(figsize=self.figsize)
        # Set up nodes' sizes.
        node_size = self._get_node_size(
            graph, node_size, kwargs.get('log_node_size', False)
        )
        # Set up nodes' color values and map.
        node_color, node_cmap = self._get_node_color(
            graph, node_color, kwargs.get('log_node_color', False)
        )
        # Set up nodes' positions and labels, if needed or relevant.
        if positions is None:
            positions = nx.fruchterman_reingold_layout(graph)
        if node_labels:
            node_labels = {node: node for node in graph.nodes}
        else:
            node_labels = None
        # Set up edges' width.
        edge_size = self._get_edge_size(
            graph, edge_size, kwargs.get('log_edge_size', False)
        )
        # Set up edges' color values and map.
        edge_color, edge_cmap = self._get_edge_color(
            graph, edge_color, kwargs.get('log_edge_color', False)
        )
        # Draw the network.
        nx.draw(
            graph, pos=positions, # labels=node_labels,
            node_size=node_size, node_color=node_color, cmap=node_cmap,
            width=edge_size, edge_color=edge_color, edge_cmap=edge_cmap
        )
        # Draw colorbar(s), if relevant.
        if node_cmap is not None:
            self._add_colorbar(figure, node_color, node_cmap)
        if edge_cmap is not None and edge_cmap != node_cmap:
            self._add_colorbar(figure, edge_color, edge_cmap)
        # Return the figure.
        return figure

    @staticmethod
    def _get_values(graph, attribute, log_values, kind):
        """Get values of a given attribute of a graph's nodes or edges."""
        # Set up attributes access depending on targetted elements.
        assert kind in ('nodes', 'edges')
        view = getattr(graph, kind)
        get_attributes = getattr(nx, 'get_%s_attributes' % kind[:-1])
        # Check attribute validity.
        if attribute not in view[list(view)[0]]:
            raise KeyError("No such %s attribute: '%s'." % (kind, attribute))
        # Get attribute values; replace missing ones with minimum, if any.
        values = pd.Series(get_attributes(graph, attribute))
        values[values == -1] = values[values > -1].min()
        # Optionally scale values using the neperian logarithm.
        if log_values:
            values[values < 1] = 1
            # false positive warning; pylint: disable=assignment-from-no-return
            values = np.log(values)
        # Return values.
        return values

    def _get_node_size(self, graph, attribute, log_values):
        """Retun the node_size argument to draw a graph."""
        # If no attribute is specified, use default size of 25.
        if attribute is None:
            return 25
        # Gather attribute values and scale sizes.
        sizes = self._get_values(graph, attribute, log_values, 'nodes')
        low, high = self.node_size_limits
        sizes = (low + (sizes - sizes.min()) * (high - low) / sizes.max())
        # Round values to integers and return them.
        return sizes.round().astype(int).values

    def _get_edge_size(self, graph, attribute, log_values):
        """Retun the width (edge size) argument to draw a graph."""
        # If no attribute is specified, use default size of 1.0.
        if attribute is None or not graph.edges:
            return 1.0
        # Gather attribute values and scale sizes.
        sizes = self._get_values(graph, attribute, log_values, 'edges')
        low, high = self.edge_size_limits
        sizes = (low + (sizes - sizes.min()) * (high - low) / sizes.max())
        # Round values to 10^-2 and return them.
        return sizes.round(2).values

    def _get_node_color(self, graph, attribute, log_values):
        """Retun the node_color and cmap arguments to draw a graph."""
        if attribute is None:
            return 'red', None
        return self._get_colors(graph, attribute, log_values, 'nodes')

    def _get_edge_color(self, graph, attribute, log_values):
        """Retun the edge_color and edge_cmap arguments to draw a graph."""
        if attribute is None or not graph.edges:
            return 'grey', None
        return self._get_colors(graph, attribute, log_values, 'edges')

    def _get_colors(self, graph, attribute, log_values, kind):
        """Set up the colors and color map for either nodes or edges."""
        # Gather attribute values, optionally scaled to logarithm.
        colors = self._get_values(graph, attribute, log_values, kind)
        # Select a colormap depending on the positivity of color values.
        # false positive warning; pylint: disable=no-member
        colormap = mpl.cm.seismic if any(colors < 0) else mpl.cm.hot_r
        # Round values to 10^-2 and return them, together with the colormap.
        return colors.round(2).values, colormap

    @staticmethod
    def _add_colorbar(figure, colors, cmap):
        """Add a colorbar to a given figure based on colors and colormap."""
        # Set up the normalized values scale based on the colormap used.
        # false positive warning; pylint: disable=no-member
        if cmap is mpl.cm.seismic:  # sentiment values in [-1, 1]
            cnorm = mpl.colors.Normalize(vmin=-1, vmax=1)
        else:  # any other quantity (only positive values)
            cnorm = mpl.colors.Normalize(vmin=0, vmax=colors.max())
        # Add a colorbar to the figure.
        lim = (len(figure.axes) - 1) * .1
        cax = figure.add_axes([lim, 0.3, 0.02, 0.6])
        mpl.colorbar.ColorbarBase(cax, cmap, cnorm, spacing='proportional')

    def make_video(self, output, imagedir, fps=1):
        """Render the network's evolution as a video.

        output   : path and name of the .mp4 video file to generate
        imagedir : path to the folder containing the pre-produced images
        fps      : number of network states to display per second of video
        """
        if not VIDEO_FEATURES:
            warnings.warn(
                '`MeTooGraphDrawer.make_video` call terminated, '
                'as opencv is not available (no cv2 Python module).'
            )
            return None
        # Setup the nodes' display positions. Setup a video writer.
        # false positives on cv2 elements; pylint: disable=no-member
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        size = tuple([value * 100 for value in self.figsize])
        video = cv2.VideoWriter(output, fourcc, fps, size, True)
        # Iteratively produce and write the graph's representation.
        for name in sorted(os.listdir(imagedir)):
            if not name.endswith('.png'):
                continue
            image = cv2.imread(os.path.join(imagedir, name))
            image = cv2.resize(image, size)
            video.write(image)
        # Save the created video.
        video.release()
        return None
