def create_weighted_average_pet(pet_file, bids_dir):

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

    meta = ReadSidecarJSON(in_file = pet_file, 
                           bids_dir = bids_dir, 
                           bids_validate = False).run()

    frames_start = np.array(meta.outputs.out_dict['FrameTimesStart'])
    frames_duration = np.array(meta.outputs.out_dict['FrameDuration'])

    frames = range(data.shape[-1])

    new_pth = os.getcwd()

    mid_frames = frames_start + frames_duration/2
    wavg = np.trapz(data[..., frames], dx=np.diff(mid_frames[frames]), axis=3)/np.sum(mid_frames)

    out_name = Path(pet_file.replace('_pet.', '_desc-wavg_pet.')).name
    out_file = os.path.join(new_pth, out_name)    
    nib.save(nib.Nifti1Image(wavg, img.affine), out_file)

    return out_file