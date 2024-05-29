#! /bin/bash
source petprep_extract_tacs_env/bin/activate

BIDS_DIR=/home/galassiae/Data/sharing/run_docker_on_this/sharing/test2
OUTPUT_DIR=$BIDS_DIR/derivatives/petprep_extract_tacs
DATE_TIME=$(date +"%F_%R")
NUM_PROCS=4

rm *crash*

# run as user
strace -o "${DATE_TIME}_fixed_strace_uid_galassiae.txt" python3 run.py --bids_dir $BIDS_DIR --output_dir $OUTPUT_DIR --wm --n_procs $NUM_PROCS --petprep_hmc --docker > run_docker_${DATE_TIME}_as_user_$NUM_PROCS.log 2>&1

rm *crash*

# run as root
strace -o "${DATE_TIME}_fixed_strace_uid_root.txt" python3 run.py --bids_dir $BIDS_DIR --output_dir $OUTPUT_DIR --wm --n_procs $NUM_PROCS --petprep_hmc --docker --run-as-root > run_docker_${DATE_TIME}_as_root_$NUM_PROCS.log 2>&1

# now let's clear out the intermediate files in the output directory
rm -rf $OUTPUT_DIR
rm -rf $BIDS_DIR/*petprep_extract_tacs*
rm *crash*

# run as user
strace -o "${DATE_TIME}_fixed_strace_uid_galassiae_cleaned.txt" python3 run.py --bids_dir $BIDS_DIR --output_dir $OUTPUT_DIR --wm --n_procs $NUM_PROCS --petprep_hmc --docker > run_docker_${DATE_TIME}_as_user_clean_$NUM_PROCS.log 2>&1

# now let's clear out the intermediate files in the output directory
rm -rf $OUTPUT_DIR
rm -rf $BIDS_DIR/*petprep_extract_tacs*
rm *crash*

# run as root
strace -o "${DATE_TIME}_fixed_strace_uid_root_clean.txt" python3 run.py --bids_dir $BIDS_DIR --output_dir $OUTPUT_DIR --wm --n_procs $NUM_PROCS --petprep_hmc --docker --run-as-root > run_docker_${DATE_TIME}_as_root_clean_$NUMP_PROCS.log 2>&1