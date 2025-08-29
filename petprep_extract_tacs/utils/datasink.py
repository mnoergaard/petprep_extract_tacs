import os
import glob
import re
import shutil
from pathlib import Path


def copy_datasink_to_derivatives(bids_dir, output_dir):
    """Copy workflow outputs from the datasink into the PET-BIDS derivatives folder."""
    datasink_dir = Path(bids_dir) / "petprep_extract_tacs_wf" / "datasink"

    pet_dirs = glob.glob(os.path.join(datasink_dir, "*_pet_file_*"))

    for pet_dir in pet_dirs:
        match_sub_id = re.search(r"sub-([A-Za-z0-9]+)", pet_dir)
        sub_id = match_sub_id.group(1)

        match_ses_id = re.search(r"ses-([A-Za-z0-9]+)", pet_dir)
        ses_id = match_ses_id.group(1) if match_ses_id else None

        file_prefix = re.search(r"_pet_file_(.*)$", os.path.basename(pet_dir)).group(1)

        if ses_id is not None:
            sub_out_dir = Path(output_dir) / f"sub-{sub_id}" / f"ses-{ses_id}"
        else:
            sub_out_dir = Path(output_dir) / f"sub-{sub_id}"

        os.makedirs(sub_out_dir, exist_ok=True)

        for root, dirs, files in os.walk(pet_dir):
            for file in files:
                if not file.startswith("."):
                    shutil.copy(
                        os.path.join(root, file),
                        os.path.join(sub_out_dir, f"{file_prefix}_{file}"),
                    )

        reg_pattern = f"sub-{sub_id}"
        if ses_id:
            reg_pattern += f"_ses-{ses_id}"
        reg_pattern += f"*{file_prefix}_from-pet_to-t1w_reg.lta"
        for reg_file in glob.glob(os.path.join(datasink_dir, reg_pattern)):
            shutil.copy(reg_file, os.path.join(sub_out_dir, os.path.basename(reg_file)))
