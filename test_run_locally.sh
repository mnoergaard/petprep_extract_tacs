#! /bin/bash
source petprep_extract_tacs_env/bin/activate

BIDS_DIR=/home/galassiae/Data/sharing/test2
OUTPUT_DIR=$BIDS_DIR/derivatives/petprep_extract_tacs

strace -o $(date '+%Y-%m-%d_%H:%M:%S')_local_strace.txt python3 run.py --bids_dir $BIDS_DIR --output_dir $OUTPUT_DIR --wm --n_procs 6 --petprep_hmc
