def create_weighted_average_pet(pet_file, json_file):

    import json
    from niworkflows.interfaces.bids import ReadSidecarJSON
    import nibabel as nib
    import numpy as np
    import os
    from pathlib import Path

    """
    Create a time-weighted average of dynamic PET data using mid-frames
    
    Arguments
    ---------
    pet_file: string
        path to input dynamic PET volume
    bids_dir: string
        path to BIDS directory containing the PET file
    """

    img = nib.load(pet_file)
    data = img.get_fdata()

    # Load the .json file
    with open(json_file, "r") as jf:
        meta = json.load(jf)

    frames_start = np.array(meta["FrameTimesStart"])
    frames_duration = np.array(meta["FrameDuration"])

    frames = range(data.shape[-1])

    new_pth = os.getcwd()

    mid_frames = frames_start + frames_duration / 2
    wavg = np.trapz(data[..., frames], dx=np.diff(mid_frames[frames]), axis=3) / np.sum(
        mid_frames
    )

    out_name = Path(pet_file.replace("_pet.", "_desc-wavg_pet.")).name
    out_file = os.path.join(new_pth, out_name)
    nib.save(nib.Nifti1Image(wavg, img.affine), out_file)

    return out_file
