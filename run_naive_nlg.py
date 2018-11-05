#!/usr/bin/env python 
"""
Run naive nlg.
"""

import sys
import json

import gen_state_attr as gsa
import setcomp as scmp
import naive_nlg as nnlg


def level_score(x):
    if x.endswith("high"):
        return 4
    if x.endswith("moderate"):
        return 3
    if x.endswith("low"):
        return 2
    if x.endswith("minimal"):
        return 1
    return 0

def grouping_score(xs):
    """
    Make grouping score.
    """

    xs = list(map(level_score, xs))

    jumping = False
    if len(xs) > 1:
        jumping = abs(xs[0] - xs[1]) > 1

    fluctuating = False
    if len(xs) > 2:
        if (xs[0] > xs[1] and xs[1] < xs[2]) or (xs[0] < xs[1] and xs[1] > xs[2]):
            fluctuating = True

    return int(jumping) * 5 + int(fluctuating) * 5 + xs[0]

def main():
    try:
        _, hhs_map_fname, bea_regions_fname, cdc_data_fname, weekend, state_attr_fname, ofname = sys.argv
    except ValueError:
        print("Usage: ./run_naive_nlg.py hhs_map.csv bea_regions.csv cdc_data.csv weekend state_attr.csv sentences.txt")
        sys.exit(1)

    gsa.gen_state_attr_df(hhs_map_fname, bea_regions_fname, cdc_data_fname, weekend, state_attr_fname)
    rows = scmp.scenario_all_combinations(state_attr_fname, None)

    for row in rows:
        row["negatives"] = [x.split(",") for x in row["negatives"]]
        row["positives"] = [x.split(",") for x in row["positives"]]

    for row in rows:
        row["text"] = nnlg.naive_nlg1(row["describing"], row["positives"], row["negatives"])

    for row in rows:
        row["rank_score"] = grouping_score(row["describing"])

    rows = sorted(rows, key=lambda x: -x["rank_score"])

    with open(ofname, "w") as fobj:
        for row in rows:
            fobj.write(json.dumps(row) + "\n")

if __name__ == "__main__":
    main()
