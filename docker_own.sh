#!/bin/bash

GIVEN_INPUT=$*
trap own_files ERR INT

own_files()
{
    platform=$(echo $GIVEN_INPUT | grep -oP 'system_platform=\K[^&]*')
    # if UID or GID is present in GIVEN_INPUT collect them and assign to variables
    if [[ $GIVEN_INPUT == *\-\-user=* ]]
    then
        uid=$(echo $GIVEN_INPUT | grep -oP '\-\-user=\K[0-9]*')
        gid=$(echo $GIVEN_INPUT | grep -oP '\-\-user=[0-9]*:\K[0-9]*')
    fi

    # dont run any of this if the host system that initiated this container isn't linux as 
    # docker running on windows or mac handles file ownership differently and we just don't 
    # need to worry about root owning files there.
    if [[ $platform != 'Linux' ]]
    then
        echo "Host system is not linux. Not changing ownership of files at /output directory" 
    else
        echo "petdeface container main process exited with code $?."
        echo "Changing ownership of files at /output directory to UID: $uid and GID: $gid"
        sudo chown $uid:$gid /output/
        sudo chown -R $uid:$gid /output
    fi

}

# run the python command minus the GID and UID arguments
echo Command Given: $GIVEN_INPUT
GIVEN_INPUT_MINUS_UID_GID_PLATFORM=$(echo $GIVEN_INPUT | sed -e 's/--user=[0-9]*:[0-9]*//' -e 's/system_platform=[^&]*//')
own_files
echo Command executing in Container: $GIVEN_INPUT_MINUS_UID_GID_PLATFORM
eval $GIVEN_INPUT_MINUS_UID_GID_PLATFORM

# own files in /output directory
own_files
