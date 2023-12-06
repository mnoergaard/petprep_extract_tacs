Node: subject_01_wf (select_files (io)
======================================


 Hierarchy : petprep_extract_tacs_wf.subject_01_wf.select_files
 Exec ID : select_files.a1


Original Inputs
---------------


* base_directory : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data
* force_lists : False
* pet_file : sub-01_ses-blocked_pet
* raise_on_empty : True
* sort_filelist : True


Execution Inputs
----------------


* base_directory : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data
* force_lists : False
* pet_file : sub-01_ses-blocked_pet
* raise_on_empty : True
* sort_filelist : True


Execution Outputs
-----------------


* brainmask_file : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data/derivatives/freesurfer/sub-01/mri/brainmask.mgz
* fs_subject_dir : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data/derivatives/freesurfer
* json_file : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data/sub-01/ses-blocked/pet/sub-01_ses-blocked_pet.json
* orig_file : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data/derivatives/freesurfer/sub-01/mri/orig.mgz
* pet_file : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data/sub-01/ses-blocked/pet/sub-01_ses-blocked_pet.nii.gz
* wm_file : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data/derivatives/freesurfer/sub-01/mri/wmparc.mgz


Runtime info
------------


* duration : 0.001948
* hostname : martinnoergaard.local
* prev_wd : /Users/martinnorgaard/Dropbox/Mac/Documents/GitHub/petprep_extract_tacs
* working_dir : /Users/martinnorgaard/Dropbox/Mac/Documents/GitHub/petprep_extract_tacs/data/petprep_extract_tacs_wf/subject_01_wf/_pet_file_sub-01_ses-blocked_pet/select_files


Environment
~~~~~~~~~~~


* CONDA_DEFAULT_ENV : petprep_extract_tacs
* CONDA_EXE : /Users/martinnorgaard/anaconda3/bin/conda
* CONDA_PREFIX : /Users/martinnorgaard/anaconda3/envs/petprep_extract_tacs
* CONDA_PREFIX_1 : /Users/martinnorgaard/anaconda3
* CONDA_PROMPT_MODIFIER : (petprep_extract_tacs) 
* CONDA_PYTHON_EXE : /Users/martinnorgaard/anaconda3/bin/python
* CONDA_SHLVL : 2
* DISPLAY : /private/tmp/com.apple.launchd.jikPtoX4Vp/org.xquartz:0
* DYLD_LIBRARY_PATH : /Applications/freesurfer/7.4.1/lib/gcc/lib:/opt/X11/lib/flat_namespace
* FIX_VERTEX_AREA : 
* FMRI_ANALYSIS_DIR : /Applications/freesurfer/7.4.1/fsfast
* FREESURFER : /Applications/freesurfer/7.4.1
* FREESURFER_HOME : /Applications/freesurfer/7.4.1
* FSFAST_HOME : /Applications/freesurfer/7.4.1/fsfast
* FSF_OUTPUT_FORMAT : nii.gz
* FSLDIR : /opt/fsl
* FSLGECUDAQ : cuda.q
* FSLLOCKDIR : 
* FSLMACHINELIST : 
* FSLMULTIFILEQUIT : TRUE
* FSLOUTPUTTYPE : NIFTI_GZ
* FSLREMOTECALL : 
* FSLTCLSH : /opt/fsl/bin/fsltclsh
* FSLWISH : /opt/fsl/bin/fslwish
* FS_OVERRIDE : 0
* FUNCTIONALS_DIR : /Applications/freesurfer/7.4.1/sessions
* HOME : /Users/martinnorgaard
* HOMEBREW_CELLAR : /opt/homebrew/Cellar
* HOMEBREW_PREFIX : /opt/homebrew
* HOMEBREW_REPOSITORY : /opt/homebrew
* INFOPATH : /opt/homebrew/share/info:
* LC_CTYPE : UTF-8
* LOCAL_DIR : /Applications/freesurfer/7.4.1/local
* LOGNAME : martinnorgaard
* MANPATH : /opt/homebrew/share/man:
* MINC_BIN_DIR : /Applications/freesurfer/7.4.1/mni/bin
* MINC_LIB_DIR : /Applications/freesurfer/7.4.1/mni/lib
* MNI_DATAPATH : /Applications/freesurfer/7.4.1/mni/data
* MNI_DIR : /Applications/freesurfer/7.4.1/mni
* MNI_PERL5LIB : /Applications/freesurfer/7.4.1/mni/lib/../Library/Perl/Updates/5.12.3
* NIPYPE_NO_ET : 1
* OLDPWD : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data
* OS : Darwin
* PATH : /Users/martinnorgaard/anaconda3/envs/petprep_extract_tacs/bin:/Users/martinnorgaard/anaconda3/condabin:/opt/homebrew/bin:/opt/homebrew/sbin:/opt/fsl/bin:/usr/local/bin:/Applications/freesurfer/7.4.1/bin:/Applications/freesurfer/7.4.1/fsfast/bin:/Applications/freesurfer/7.4.1/mni/bin:/Applications/CMake.app/Contents/bin:/usr/local/ants/bin:/usr/local/infomap:/Applications/AIR5.3.0/bin:/Users/martinnorgaard/Documents/Work/Code/volio/mriwarp-1.52:/Applications/Octave-6.3.0.app/Contents/MacOS/applet:/Applications/PETPVC-1.2.10/bin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/opt/X11/bin:/Library/Apple/usr/bin:/Users/martinnorgaard/afni
* PERL5LIB : /Applications/freesurfer/7.4.1/mni/lib/../Library/Perl/Updates/5.12.3
* PS1 : (petprep_extract_tacs) $ 
* PWD : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs
* SHELL : /bin/bash
* SHLVL : 1
* SSH_AUTH_SOCK : /private/tmp/com.apple.launchd.gYwZbsMErK/Listeners
* SUBJECTS_DIR : /Applications/freesurfer/7.4.1/subjects
* TERM : xterm-256color
* TERM_PROGRAM : Apple_Terminal
* TERM_PROGRAM_VERSION : 450
* TERM_SESSION_ID : CAF401A8-796A-4896-B0EC-497DA71F3377
* TMPDIR : /var/folders/0d/tx6_gy7951749z57rjjkkl_m0000gn/T/
* USER : martinnorgaard
* XPC_FLAGS : 0x0
* XPC_SERVICE_NAME : 0
* _ : /Users/martinnorgaard/anaconda3/envs/petprep_extract_tacs/bin/python3
* _CE_CONDA : 
* _CE_M : 
* __CFBundleIdentifier : com.apple.Terminal
* __CF_USER_TEXT_ENCODING : 0x1F5:0x0:0x9

