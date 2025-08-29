.. _usage:

This will run the app on your BIDS dataset and save the output to the specified directory. Additional region-specific and smoothing options can be specified as detailed below.

usage
=====

Required Arguments
------------------

Here's a detailed look at all the options you can use with this BIDS App:

``bids_dir``
    This is the directory with your input dataset formatted according to the BIDS standard. This argument is required.

``output_dir``
    This is the directory where the output files should be stored. If you are running group level analysis, this folder should be prepopulated with the results of the participant level analysis.

``analysis_level``
    This argument defines the level of the analysis that will be performed. Multiple participant level analyses can be run independently (in parallel) using the same output_dir. The default is 'participant'. The choices are 'participant' and 'group'.

Processing options
------------------

``--participant_label``
    This argument specifies the label(s) of the participant(s) that should be analyzed. The label corresponds to sub-<participant_label> from the BIDS spec (so it does not include "sub-"). If this parameter is not provided, all subjects should be analyzed. Multiple participants can be specified with a space-separated list.

``--participant_label_exclude``
    This argument specifies the label(s) of the participant(s) that should *not* be analyzed. If omitted all subjects should be analyzed. Multiple participants can be specified with a space-separated list.

``--session_label``
    Similar to ``--participant_label``, used to specify which sessions to include. Multiple sessions can be provided via a space-separated list.

``--session_label_exclude``
    Similar to ``--participant_label_exclude``, used to specify session(s) that should *not* be analyzed. If omitted all sessions should be analyzed. Multiple sessions can be specified with a space-separated list.

``--n_procs``
    This argument sets the number of processors to use when running the workflow. The default is 2.

Region extraction options
-------------------------

``--gtm``, ``--brainstem``, ``--thalamicNuclei``, ``--hippocampusAmygdala``, ``--wm``, ``--raphe``, ``--limbic``
    These options, when specified, instruct the workflow to extract time activity curves from the corresponding brain regions.

Smoothing and output space options (surface and/or volume)
----------------------------------------------------------

``--surface``, ``--surface_smooth`` (e.g. ``--surface_smooth 10``), ``--volume``, ``--volume_smooth`` (e.g. ``--volume_smooth 10``)

Partial Volume Correction
-------------------------

``--pvc {gtm, agtm}``, ``--psf`` (initial PSF guess for ``--pvc agtm``, e.g. ``--psf 3``)

Advanced options
----------------

``--petprep_hmc``
    When specified, the workflow will use outputs from petprep_hmc as input.

``--skip_bids_validator``
    This argument, when specified, will skip the BIDS dataset validation step.

``--merge_runs``
    Option to merge TACs across runs for each subject within a single session.

Docker options
--------------

``--docker``
    Indicates the script will run within a Docker container that contains all of the necessary dependencies for this project. A version of FreeSurfer should still be installed along with a valid license. If you have difficulty using this extra option below is an example of an "unwrapped" command to execute this pipeline in Docker.

.. code-block:: bash

    docker run -a stderr -a stdout --rm \ 
    -v /Users/user1/data/dataset/:/bids_dir \
    -v /Users/user1/data/dataset/derivatives/petprep_extract_tacs:/output_dir \
    -v $PWD:/workdir -v /Users/user1/Projects/petprep_extract_tacs:/petprep_extract_tacs \
    -v /Applications/freesurfer/7.4.1/license.txt:/opt/freesurfer/license.txt \
    --platform linux/amd64 \
    petprep_extract_tacs \
    --bids_dir /bids_dir /output_dir participant --n_procs 4 system_platform=Darwin

    The docker container can be built with the following command:

.. code-block:: bash

    cd petprep_extract_tacs && docker build . -t petprep_extract_tacs

    We specify the platform as linux/amd64 since running with a single architecture typically leads to greater reliability. That said, this pipeline has been developed and tested on both x86 Linux and Apple Silicon.

``--run_as_root``
    Runs the script as root if executed within Docker, by default the ``--docker`` flag will attempt to run the container as the calling user.

Version
-------

``-v``, ``--version``
    This argument displays the current version of the PETPrep extract time activity curves BIDS-App.
