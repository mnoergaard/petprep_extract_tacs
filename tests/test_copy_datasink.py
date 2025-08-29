import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from petprep_extract_tacs.utils.datasink import copy_datasink_to_derivatives


def test_copy_datasink_to_derivatives(tmp_path):
    bids_dir = tmp_path
    datasink = bids_dir / "petprep_extract_tacs_wf" / "datasink"
    pet_dir = datasink / "sub-01_ses-01_pet_file_tracer"
    pet_dir.mkdir(parents=True)

    (pet_dir / "file1.txt").write_text("foo")
    (pet_dir / "file2.nii").write_text("bar")

    reg_file = datasink / "sub-01_ses-01_tracer_from-pet_to-t1w_reg.lta"
    reg_file.write_text("reg")

    output_dir = bids_dir / "derivatives" / "petprep_extract_tacs"
    copy_datasink_to_derivatives(bids_dir, output_dir)

    out_dir = output_dir / "sub-01" / "ses-01"
    assert (out_dir / "tracer_file1.txt").exists()
    assert (out_dir / "tracer_file2.nii").exists()
    assert (out_dir / reg_file.name).exists()
