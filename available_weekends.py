"""
List the available weekends from the cdc data.
"""

import sys
import pandas as pd

def main():
    _, cdc_data_fname = sys.argv

    cdc_data_df = pd.read_table(cdc_data_fname, sep="|")
    cdc_data_df = cdc_data_df.assign(weekend=pd.to_datetime(cdc_data_df.weekend))

    all_weekends = sorted(set(cdc_data_df.weekend))
    for weekend in all_weekends:
        print(weekend)

if __name__ == "__main__":
    main()
