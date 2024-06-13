import pandas
import pathlib
import bids
import argparse
import os
from difflib import get_close_matches
from pprint import pprint
import re

from petprep_extract_tacs.bids import collect_participants


def collect_and_merge_tsvs(
    bids_dir, tsv_type="tacs", subjects=[], delete_extra_runs=False, **kwargs
):
    """
    Collect and merge all tsv's that should be combined across a runs. This is
    function is primarily aimed at combining PET time activity curve (TACS) for
    long scans present in a BIDS directory or BIDS subject directory.

    The tsv_type parameter can be changed to specify a deseg.tsv or morph.tsv where
    appropriate.

    Parameters
    ----------
    bids_dir : str
        Path to the BIDS directory.
    tsv_type : str
        Type of TSV file to output to merge corresponding the bids suffix.
    subjects : list
        List of subjects to run this function on.
    delet_extra_runs : bool
        If True, the tsv's will be merged into a single file, if False this function will not merge, but instead
        only keep the first copy of the tsvs that are found and remove the run-[0-9] from the filename. This is
        useful for dseg and morph tsvs.
    **kwargs : dict
        Keyword arguments to pass to pandas.read_csv.

    Returns
    -------
    pandas.DataFrame
        Collected TSVs.
    """

    # get every file in the bids directory with a tacs suffix
    all_tsvs = []
    for root, folders, files in os.walk(bids_dir):
        for f in files:
            full_file_path = os.path.join(root, f)
 
            if f.endswith(
                ".tsv"
            ):  # and os.path.join('derivatives', 'petprep_extract_tacs') in full_file_path:
                all_tsvs.append(full_file_path)

    # filter out any files that don't have petprep_extract_tacs/derivatives in the path
    all_tsvs = [
        f for f in all_tsvs if os.path.join("derivatives", "petprep_extract_tacs") in f
    ]

    # filter to only files that contain _run- in the filename
    all_tsvs = [f for f in all_tsvs if "_run-" in f]

    # filter to only files that contain the tsv_type in the filename
    all_tsvs = [f for f in all_tsvs if tsv_type in f]

    all_tsvs.sort()

    # create a unix style * string for each tac file by replacing the part of the
    # path "_run-01_" with "_run-*_" instead.
    # this will allow us to use fnmatch to find all of the files that match the pattern
    unix_style_tsvs = [re.sub(r"_run-[0-9]_", "_run-[0-9]_", f) for f in all_tsvs]
    unix_style_tsvs = list(set(unix_style_tsvs))
    unix_style_tsvs.sort()

    # now we make sure that the regex string we made for each unix style tac can handle the "." and "/" characters
    unix_style_tsvs = [re.sub(r"\.", r"\.", f) for f in unix_style_tsvs]  # escape .
    unix_style_tsvs = [re.sub(r"/", r"\/", f) for f in unix_style_tsvs]  # escape /

    # now we use glob to find all of the files that match the pattern
    to_be_merged_tsvs = {}

    for t in unix_style_tsvs:
        to_be_merged_tsvs[t] = []
        for tsv in all_tsvs:
            if re.match(t, tsv):
                to_be_merged_tsvs[t].append(tsv)

    # we want to reorganize this to be merged and label the keys with the subject id instead of the
    # full file path/regex string as we used before.

    subjects_to_be_merged = {}
    for k, v in to_be_merged_tsvs.items():
        for tsv in v:
            # locate the subject id by doing a regex search for sub-[a-zA-Z0-9]+_
            subject = re.search(r"sub-[a-zA-Z0-9]+_", tsv).group(0)[:-1]
            subject = subject.split("-")[1]
            if not subjects_to_be_merged.get(subject, None):
                subjects_to_be_merged[subject] = {k: []}
            if not subjects_to_be_merged[subject].get(k, None):
                subjects_to_be_merged[subject][k] = []
            subjects_to_be_merged[subject][k].append(tsv)

    # now we only focuse on subjects that are specified if that's given in thes arguments
    # subjects = [01, 02, ...] for this function
    if subjects != []:
        subjects_to_remove = list(set(subjects_to_be_merged.keys() - set(subjects)))
        for s in subjects_to_remove:
            subjects_to_be_merged.pop(s, None)

    merged_tsvs = []
    for subject, set_of_tacs in subjects_to_be_merged.items():
        for tsvs in set_of_tacs.values():
            if not delete_extra_runs:
                merged_dataframes = merge_tsvs(*v)
            else:
                merged_dataframes = pandas.read_csv(tsvs[0], sep="\t", **kwargs)
            # create a filename for these merged tacs by removing the _run-[0-9] from the filename
            # this will allow us to save the merged tacs to a single file
            combined_file_name = re.sub(r"_run-[0-9]_", "_", tsvs[0])
            merged_dataframes.to_csv(
                combined_file_name, sep="\t", index=False, **kwargs
            )
            merged_tsvs.append(combined_file_name)
            for tsv in tsvs:
                os.remove(tsv)

    return merged_tsvs


def merge_tsvs(*args, **kwargs):
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
        tac = pandas.read_csv(arg, sep="\t", **kwargs)
        tacs.append(tac)
    tacs = pandas.concat(tacs, ignore_index=True)
    return tacs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge TACs from different files into a single file."
    )
    parser.add_argument("bids_dir", type=str, help="Path to the BIDS directory.")
    parser.add_argument(
        "--tsv_type",
        type=str,
        default="tacs",
        help="Type of TSV file to output to merge.\nDefault: tacs   ",
    )
    parser.add_argument(
        "--subjects",
        type=str,
        nargs="+",
        help="List of subjects to merge tsvs to merge.",
        default=[],
    )
    parser.add_argument(
        "--delete-extra-runs",
        action="store_true",
        help="If True, the extra runs will be deleted and only the first run will be kept. Thank you inheritance!",
    )
    args = parser.parse_args()

    tacs = collect_and_merge_tsvs(
        args.bids_dir,
        tsv_type=args.tsv_type,
        subjects=args.subjects,
        delete_extra_runs=args.delete_extra_runs,
    )
