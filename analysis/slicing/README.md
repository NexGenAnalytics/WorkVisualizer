## Instructions for Use

There are some new dependencies in `analysis/slicing/requirements.txt`.

`cd` to this directory and then run `pip install -r requirements.txt` to install them.

You will also need [`stumpy`](https://stumpy.readthedocs.io/en/latest/) installed, if you are running the time series analysis.

```
conda install -c conda-forge stumpy
```

If the import doesn't work for CUDA-related reasons, follow the "Short-Term Change" instructions [here](https://github.com/TDAmeritrade/stumpy/issues/314#issuecomment-761001109) (you'll need to `git clone` the stumpy repo and make a small change).

## Explanations

There are two approaches to slicing in this directory: 1) graph-pattern matching and 2) time series analysis.

The scripts related to graph-pattern matching are prefixed with `g`, and the script for time series analysis start with `t`.

Follow the order in the script names, like so:

#### Graph-Pattern Matching

Run `g1_...`, then `g2_...`, then `g3_...`

#### Time Series Analysis

Run `t1_...`, then `t2_...`

You will have to change the scripts themselves to point to the correct directories in your filestem.

## General Notes

#### Graph-Pattern Matching

The idea here is to find repeated patterns (or sub-graphs) within the program's full call graph. This would provide a topological idea of the "slice", based on the nodes/edges rather than timing.

#### Time Series Analysis

Lots of libraries (`stumpy`, e.g) and analysis techniques have been developed for analyzing and deconstructing patterns in time series data. The main idea is to restructure our data into a time series so that we can leverage these tools.

Here are the steps currently implemented in the time series analysis pipeline:
1. Sampling the data: This is how we generate the time series data. We break the full duration of the program into `n` discrete bins and then count how many function calls are present in each bin. This generates "Discrete Time Series Data", as mentioned [here](https://www.geeksforgeeks.org/time-series-data-visualization-in-python/).

2. Fourier Analysis: This gives us a guess for the `window_size`, used in the next step.

3. Stumpy: Given a `window_size` (the amount of data points that may comprise a pattern), `stumpy` is supposedly able to identify motifs (recurring patterns) and anomalies in the time series.

4. That's all that I've written so far; the original plan was to use the pattern found by `stumpy` to train a neural network, which would allow for more flexibility in determining what constitutes a time step. That may be outside of the scope of Phase I though.

