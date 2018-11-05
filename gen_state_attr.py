"""
Generate state attributes matrix.
"""
# pylint: disable=missing-docstring

import sys
from pathlib import Path

import pandas as pd
import numpy as np

STATE_NAME_TO_STATE_CODE = None
NUMERIC_LEVEL_TO_STRING_LEVEL = None
STRING_LEVEL_TO_NUMERIC_LEVEL = None

def get_area_id_state_code_map(df):
    df = df[["area_id", "state_code"]]
    df = df.set_index("area_id")
    df = df.sort_index()
    return df.state_code

def get_level_level_label_map(df):
    df = df[["activity_level", "activity_level_label"]]
    df = df.drop_duplicates(["activity_level"])
    df = df.set_index("activity_level")
    df = df.sort_index()
    return df.activity_level_label

def get_state_activity_df(df, weekend):
    df = df[df["weekend"] == weekend]
    df = df[["statename", "activity_level"]]
    df = df.copy()

    df["state"] = df["statename"].map(STATE_NAME_TO_STATE_CODE)
    df["activity"] = df["activity_level"].map(NUMERIC_LEVEL_TO_STRING_LEVEL)
    df = df.dropna()

    df["val"] = 1
    df = df.pivot(index="state", columns="activity", values="val")
    df = df.fillna(0)

    for column in np.unique(NUMERIC_LEVEL_TO_STRING_LEVEL):
        if column in df.columns:
            df[column] = df[column].astype(np.int64)
        else:
            df[column] = 0

    df = df.rename(columns={k: "_".join(k.lower().split()) for k in df.columns})
    df = df[sorted(df.columns)]
    df = df.drop("insufficient_data", axis=1)
    return df

def get_state_past_activity_df(df, weekend, n):
    weekend = pd.to_datetime(weekend)
    weekend += n * pd.to_timedelta("7days")
    df = get_state_activity_df(df, weekend)

    if n == -1:
        new_columns = {k: f"was_{k}" for k in df.columns}
    elif n < -1:
        n = n + 1
        new_columns = {k: f"was{-n}_{k}" for k in df.columns}
    else:
        raise ValueError(n)

    df = df.rename(columns=new_columns)
    return df

def get_state_activity_numeric_df(df, weekend):
    df = df[df["weekend"] == weekend]
    df = df[["statename", "activity_level"]]
    df = df.copy()

    df["state"] = df["statename"].map(STATE_NAME_TO_STATE_CODE)
    df["activity"] = df["activity_level"].map(NUMERIC_LEVEL_TO_STRING_LEVEL)
    df = df.dropna()

    df = df[["state", "activity"]]
    df["activity"] = df["activity"].map(STRING_LEVEL_TO_NUMERIC_LEVEL)
    df = df.sort_values("state")
    df = df.set_index("state")

    return df.activity
def get_state_change_df(df, cur_weekend):
    cur_weekend = pd.to_datetime(cur_weekend)
    next_weekend = cur_weekend + pd.to_timedelta("7days")
    prev_weekend = cur_weekend - pd.to_timedelta("7days")

    past = get_state_activity_numeric_df(df, prev_weekend)
    present = get_state_activity_numeric_df(df, cur_weekend)
    future = get_state_activity_numeric_df(df, next_weekend)

    df = {
        "has_increased": present > past,
        "has_decreased": present < past,
        "has_been_stable": past == present,

        "will_increase": future > present,
        "will_decrease": future < present,
        "will_be_stable": future == present
    }
    df = {k: v.astype(float) for k, v in df.items()}
    df = pd.DataFrame(df)
    df = df.fillna(0).copy()
    for column in df.columns:
        df[column] = df[column].astype(np.int64)
    df = df[sorted(df.columns)]
    return df

def get_state_bea_regions_matrix(df):
    df = df[["Abbreviation", "Region code"]]
    df = df.rename(columns={"Abbreviation": "abbr", "Region code": "region_code"})
    regions = df.drop_duplicates(subset=["region_code"])
    df = df[~df.abbr.isin(regions.abbr)]
    df = pd.merge(df, regions, on="region_code")
    df["val"] = 1.0
    df = df.pivot(index="abbr_x", columns="abbr_y", values="val")
    df = df.fillna(0.0).copy()
    for column in df.columns:
        df[column] = df[column].astype(np.int64)
    df = df[sorted(df.columns)]
    return df

def initialize(hhs_map_df, cdc_data_df):
    global STATE_NAME_TO_STATE_CODE
    global NUMERIC_LEVEL_TO_STRING_LEVEL
    global STRING_LEVEL_TO_NUMERIC_LEVEL

    NUMERIC_LEVEL_TO_STRING_LEVEL = get_level_level_label_map(cdc_data_df)

    STRING_LEVEL_TO_NUMERIC_LEVEL = NUMERIC_LEVEL_TO_STRING_LEVEL.drop_duplicates()
    STRING_LEVEL_TO_NUMERIC_LEVEL = STRING_LEVEL_TO_NUMERIC_LEVEL.reset_index().set_index("activity_level_label")
    STRING_LEVEL_TO_NUMERIC_LEVEL = STRING_LEVEL_TO_NUMERIC_LEVEL["activity_level"]

    STATE_NAME_TO_STATE_CODE = hhs_map_df[["state_name", "state_code"]]
    STATE_NAME_TO_STATE_CODE = STATE_NAME_TO_STATE_CODE.set_index("state_name")
    STATE_NAME_TO_STATE_CODE = STATE_NAME_TO_STATE_CODE.state_code

def gen_state_attr_df(hhs_map_fname, bea_regions_fname, cdc_data_fname, weekend, state_attr_fname):

    hhs_map_colnames = "area_id region state_code state_name".split()
    hhs_map_df = pd.read_csv(hhs_map_fname, names=hhs_map_colnames)

    bea_regions_df = pd.read_csv(bea_regions_fname)

    cdc_data_df = pd.read_table(cdc_data_fname, sep="|")
    cdc_data_df = cdc_data_df.assign(weekend=pd.to_datetime(cdc_data_df.weekend))

    weekend = pd.to_datetime(weekend)
    all_weekends = sorted(set(cdc_data_df.weekend))

    if weekend not in all_weekends:
        print("Data not available for weekend:", weekend)
        sys.exit(1)

    initialize(hhs_map_df, cdc_data_df)

    state_activity_df = get_state_activity_df(cdc_data_df, weekend)
    state_change_df = get_state_change_df(cdc_data_df, weekend)

    state_past1_activity_df = get_state_past_activity_df(cdc_data_df, weekend, -1)
    state_past2_activity_df = get_state_past_activity_df(cdc_data_df, weekend, -2)
    state_past3_activity_df = get_state_past_activity_df(cdc_data_df, weekend, -3)
    state_past4_activity_df = get_state_past_activity_df(cdc_data_df, weekend, -4)
    state_past5_activity_df = get_state_past_activity_df(cdc_data_df, weekend, -5)
    state_past53_activity_df = get_state_past_activity_df(cdc_data_df, weekend, -53)

    state_past_activity_df = state_past1_activity_df.join(state_past2_activity_df)
    state_past_activity_df = state_past_activity_df.join(state_past3_activity_df)
    state_past_activity_df = state_past_activity_df.join(state_past4_activity_df)
    state_past_activity_df = state_past_activity_df.join(state_past5_activity_df)
    state_past_activity_df = state_past_activity_df.join(state_past53_activity_df)

    bea_regions_mat_df = get_state_bea_regions_matrix(bea_regions_df)

    attr_df = pd.merge(state_activity_df, state_change_df, left_index=True, right_index=True)
    attr_df = pd.merge(attr_df, state_past_activity_df, left_index=True, right_index=True)
    attr_df = pd.merge(attr_df, bea_regions_mat_df, left_index=True, right_index=True)

    attr_df.to_csv(state_attr_fname)

def main():
    data_dir = Path("~/data/epi-summary").expanduser().absolute()

    hhs_map_fname = data_dir / "state_hhs_map.csv"
    bea_regions_fname = data_dir / "US_BEA_regions.csv"
    cdc_data_fname = data_dir / "cdc-state-level-20180622.csv"

    weekend = "2018-03-17"

    # Outputs
    state_attr_fname = "state_attr.csv"

    gen_state_attr_df(hhs_map_fname, bea_regions_fname, cdc_data_fname, weekend, state_attr_fname)

if __name__ == "__main__":
    main()
