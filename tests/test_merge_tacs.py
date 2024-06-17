import pytest
import shutil
import tempfile
import os
import sys
import glob
import pandas
import subprocess
import pathlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path
from petprep_extract_tacs.utils.merge_tacs import collect_and_merge_tsvs, merge_tsvs

test_data = Path(__file__).parent.parent / "data"


def test_collect_and_merge_tsvs():
    with tempfile.TemporaryDirectory() as tempdir:
        subprocess.run(f"cp -r {test_data}/* {tempdir}", shell=True)
        # get all tsvs with glob
        all_tsvs = glob.glob(f"{tempdir}/**/*.tsv", recursive=True)

        # ignore everthing that doesn't have run in it.
        unmerged_run_tsvs = [tsv for tsv in all_tsvs if "_run-" in tsv]
        unmerged_run_tsvs.sort()

        # get base folder name of run tsvs
        base_folder = pathlib.Path(unmerged_run_tsvs[0]).parent.resolve()

        # read all tsvs in with read.csv as tsv files and use their keys as filenames
        unmerged_run_tsvs = {
            os.path.basename(tsv): pandas.read_csv(tsv, sep="\t")
            for tsv in unmerged_run_tsvs
        }

        # run collect_and_merge_tsvs on tempdir
        merged_tsvs = collect_and_merge_tsvs(bids_dir=tempdir)
        merged_tsvs = {tsv: pandas.read_csv(tsv, sep="\t") for tsv in merged_tsvs}

        # check that the merged tsvs are the concatentaion of the unmerged tac tsvs same as the unmerged run tsvs
        tacs = [unmerged_run_tsvs[tsv] for tsv in unmerged_run_tsvs if "tacs" in tsv]

        # add up lengths of split tacs
        total_rows = sum([len(tac) for tac in tacs])

        test_merge = pandas.concat(tacs, ignore_index=True)

        # get the tac file that was merged
        merged_tac = None
        for tsv in merged_tsvs:
            if "tacs" in tsv:
                merged_tac = merged_tsvs[tsv]
            if "morph" in tsv:
                deduplicated_morph = merged_tsvs[tsv]
            if "dseg" in tsv:
                deduplicated_dseg = merged_tsvs[tsv]

        assert total_rows == len(merged_tac)
        assert test_merge.equals(merged_tac)

        # get unmerged morph tsvs
        unmerged_morphs = [
            unmerged_run_tsvs[tsv] for tsv in unmerged_run_tsvs if "morph" in tsv
        ]
        for unmerged_morph in unmerged_morphs:
            assert unmerged_morph.equals(deduplicated_morph)

        # check that the deduplicated dseg tsvs are the same as the unmerged dseg tsvs
        unmerged_dsegs = [
            unmerged_run_tsvs[tsv] for tsv in unmerged_run_tsvs if "dseg" in tsv
        ]
        for unmerged_dseg in unmerged_dsegs:
            assert unmerged_dseg.equals(deduplicated_dseg)

        subprocess.run(f"tree {tempdir}/derivatives/petprep_extract_tacs", shell=True)
        subprocess.run(
            f"cp -r {tempdir}/derivatives/petprep_extract_tacs ~/Desktop/check_this/",
            shell=True,
        )
