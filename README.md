How to run:

python ./run_naive_nlg.py state_hhs_map.csv US_BEA_regions.csv cdc-state-level-20180622.csv 20180120 state_attr.csv sentences.txt >> outputfile

20180120 (01/20/2018) corresponds to an epi-week for which we are generating the summary.
outputfile : outputs descriptions for all target sets
sentences.txt: contains descriptions generated using simple nlg.
