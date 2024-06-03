import pandas
import pathlib
import bids
import argparse

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


def collect_and_merge_tacs(bids_dir, subject='', session='', **kwargs):
    """
    Collect and merge all TACs from a BIDS directory or BIDS subject directory.

    Parameters
    ----------
    bids_dir : str
        Path to the BIDS directory.
    subject : str
        Subject label.
    session : str
        Session label.
    run : str
        Run label.
    **kwargs : dict
        Keyword arguments to pass to pandas.read_csv.

    Returns
    -------
    pandas.DataFrame
        Collected TACs.
    """
    layout = bids.BIDSLayout(bids_dir, derivatives=True)
    if subject == '':
        participants = collect_participants(bids_dir)
        tacs = []
        for subject in participants:
            tacs.append(collect_and_merge_tacs(bids_dir, f"sub-{subject}", session, **kwargs))
        merge_tacs(tacs, **kwargs)
    elif subject != '' and session != '':
        tacs = layout.get(subject=subject, suffix='tac', extension='tsv', return_type='file')
        tacs = merge_tacs(*tacs, **kwargs)
    elif subject != '' and session != '':
        # get a list of all the sessions per subject and merge those tacs session by session
        tacs = layout.get(subject=subject, session=session, suffix='tac', extension='tsv', return_type='file')
    return tacs


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
        tac = pandas.read_csv(arg, **kwargs)
        tacs.append(tac)
    tacs = pandas.concat(tacs, ignore_index=True)
    return tacs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge TACs from different files into a single file.')
    parser.add_argument('--bids_dir', type=str, help='Path to the BIDS directory.')
    parser.add_argument('--subject', type=str, help='Subject label.')
    parser.add_argument('--session', type=str, help='Session label.')
    parser.add_argument('--tacs', type=str, nargs='+', help='TAC file paths to merge.')
    parser.add_argument('--output', type=str, help='Output file path.')
    args = parser.parse_args()

    if not args.tacs:
        tacs = collect_and_merge_tacs(args.bids_dir, args.subject, args.session)
    else:
        tacs = merge_tacs(*args.tacs)
    tacs.to_csv(args.output, sep='\t', index=False)

