# #MeToo Twitter database network analysis tools.

Implementation realized in the context of scholar project on network analysis.
Database-specific implementation, meant for work on a public dataset published
[here](https://data.world/from81/390k-metoo-tweets-cleaned) by Kai Hirota,
which contains pre-processed tweets collected between November 29th and
December 25th, 2017 by Brett Turner (initial source
[here](https://data.world/balexturner/390-000-metoo-tweets)).


#### Results-production pipepline

To run a basic results-production pipeline, simply download a copy of the
code and of the dataset, then edit the `pipepline.py` file to set up the
constants appropriately (lines 13 to 15) and run `python3 pipepline.py`.

This will build graphs set, output .gexf files of the final network states
for exploitation with Gephi, output visualizations of the network's evolution
(including a video file if the `cv2` package is installed) and finally dump
to a .pickle file the graphs built and metrics computed to help characterize
them and their evolution.


#### Organization of the implemented tools

The code is structured in classes that all aim at a specific part of the
data processing, vizualisation and analysis pipepline:

* Data processing classes:
  * `MeTooDataExtractor` extracts enriched data from the initial SQLite
    file to csv files
  * `MeTooDataLoader` is a backend class for the former


* Network analysis classes:
  * `MeTooGraphBuilder` builds `networkx.DiGraph` instances based
    on the extracted data
  * `MeTooGraphDrawer` draws visual representations of the former graphs
  * `MeTooGraphAnalyzer` computes network-wide and user-wise statistics
    characterizing the former graphs

#### License

Copyright 2019 Paul Andrey

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
