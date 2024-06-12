import pandas
import pathlib
import bids
import argparse
import os
from difflib import get_close_matches
from pprint import pprint
import fnmatch
import re
import glob

from petprep_extract_tacs.bids import collect_participants

def offset_to_one_time_zero(bids_dir, *tacs, inplace=False):
    """
    Finds the corresonding pet json sidecar files for each TAC file and extracts the time zero from each run.
    Then offsets the following runs to match the time zero of run 1.

    Parameters
    ----------
    bids_dir : str
        path to a BIDS dataset
    tacs : list
        list of TAC file paths
    inplace : bool
        if True, the TAC files will be modified in place defaults to false
    
    Returns
    -------
    offset_tacs : dict
        dictionary of tacs provided via *tacs along with their offset applied to the frame start and end times
    """

    # use pybids to get all of the entities for each TAC file
    layout = bids.BIDSLayout(bids_dir, derivatives=True)


def collect_and_merge_tacs(bids_dir, **kwargs):
    """
    Collect and merge all TACs from a BIDS directory or BIDS subject directory.

    Parameters
    ----------
    bids_dir : str
        Path to the BIDS directory.
    **kwargs : dict
        Keyword arguments to pass to pandas.read_csv.

    Returns
    -------
    pandas.DataFrame
        Collected TACs.
    """
    
    # get every file in the bids directory with a tacs suffix
    all_tacs = []
    for root, folder, files in os.walk(bids_dir):
        for f in files:
            if 'tacs' in f:
                all_tacs.append(os.path.join(root, f))
    
    all_tacs.sort()
    
    # create a unix style * string for each tac file by replacing the part of the 
    # path "_run-01_" with "_run-*_" instead.
    # this will allow us to use fnmatch to find all of the files that match the pattern
    unix_style_tacs = [re.sub(r'_run-[0-9]_', '_run-[0-9]_', f) for f in all_tacs]
    unix_style_tacs = list(set(unix_style_tacs))
    unix_style_tacs.sort()
    
    # now we make sure that the regex string we made for each unix style tac can handle the "." and "/" characters
    unix_style_tacs = [re.sub(r'\.', r'\.', f) for f in unix_style_tacs] # escape .
    unix_style_tacs = [re.sub(r'/', r'\/', f) for f in unix_style_tacs] # escape /

    # now we use glob to find all of the files that match the pattern
    to_be_merged_tacs = {}

    for t in unix_style_tacs:
        to_be_merged_tacs[t] = []
        for tac in all_tacs:
            if re.match(t, tac):
                to_be_merged_tacs[t].append(tac)
    for values in to_be_merged_tacs.values():
        print("These tacs will be merged:")
        for v in values:
            print(v)
    values = list(to_be_merged_tacs.values())

    merged_tacs = []
    for v in values:
            tacs = merge_tacs(*v)
            # create a filename for these merged tacs by removing the _run-[0-9] from the filename
            # this will allow us to save the merged tacs to a single file
            combined_file_name = re.sub(r'_run-[0-9]_', '_', v[0])
            tacs.to_csv(combined_file_name, sep='\t', index=False, **kwargs)
            merged_tacs.append(combined_file_name)
            for t in v:
                os.remove(t)

    return merge_tacs

def merge_tacs(*args, **kwargs):
    """
    Merge TACs from different files into a single file.

    Parameters
    ----------
    *args : list
        List of tsv tac file paths to merge.
    **kwargs : dict
        Keyword arguments to pass to pandas.read_csv.

    Returns
    -------
    pandas.DataFrame
        Merged TACs.
    """
    tacs = []    
    args = [pathlib.Path(arg).resolve() for arg in args if pathlib.Path(arg).exists()]

    for arg in args:
        tac = pandas.read_csv(arg, sep='\t', **kwargs)
        tacs.append(tac)
    tacs = pandas.concat(tacs, ignore_index=True)
    return tacs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge TACs from different files into a single file.')
    parser.add_argument('bids_dir', type=str, help='Path to the BIDS directory.')
    args = parser.parse_args()

    tacs = collect_and_merge_tacs(args.bids_dir)


