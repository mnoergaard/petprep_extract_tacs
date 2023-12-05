import argparse
import os
from pathlib import Path
import glob
import re
import shutil
import json
import pkg_resources
from bids import BIDSLayout
from nipype.interfaces.utility import IdentityInterface, Merge
from nipype.pipeline import Workflow
from nipype import Node, Function, DataSink
from nipype.interfaces.io import SelectFiles
from niworkflows.utils.misc import check_valid_fs_license
from petprep_extract_tacs.utils.pet import create_weighted_average_pet
from nipype.interfaces.freesurfer import MRICoreg, ApplyVolTransform, MRIConvert, Concatenate
from petprep_extract_tacs.interfaces.petsurfer import GTMSeg, GTMPVC
from petprep_extract_tacs.interfaces.segment import SegmentBS, SegmentHA_T1, SegmentThalamicNuclei, MRISclimbicSeg
from petprep_extract_tacs.interfaces.fs_model import SegStats
from petprep_extract_tacs.utils.utils import ctab_to_dsegtsv, avgwf_to_tacs, summary_to_stats, gtm_to_tacs, gtm_stats_to_stats, gtm_to_dsegtsv, limbic_to_dsegtsv, limbic_to_stats, plot_reg

from petprep_extract_tacs.bids import collect_data

__version__ = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'version')).read()


def main(args):
    # Check whether BIDS directory exists and instantiate BIDSLayout
    if os.path.exists(args.bids_dir):
        if not args.skip_bids_validator:
            layout = BIDSLayout(args.bids_dir, validate=True)
        else:
            layout = BIDSLayout(args.bids_dir, validate=False)
    else:
        raise Exception('BIDS directory does not exist')

    # Check whether FreeSurfer license is valid
    if check_valid_fs_license() is not True:
        raise Exception('You need a valid FreeSurfer license to proceed!')

    # Get all PET files
    if args.participant_label is None:
        args.participant_label = layout.get(suffix='pet', target='subject', return_type='id')

    # Create derivatives directories
    if args.output_dir is None:
        output_dir = os.path.join(args.bids_dir, 'derivatives', 'petprep_extract_tacs')
    else:
        output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)

    # Run ANAT workflow
    anat_main = init_anat_wf()
    anat_main.run(plugin='MultiProc', plugin_args={'n_procs': int(args.n_procs)})

    # Run PET workflow
    main = init_petprep_extract_tacs_wf()
    main.run(plugin='MultiProc', plugin_args={'n_procs': int(args.n_procs)})

    # Remove temp outputs
    shutil.rmtree(os.path.join(args.bids_dir, 'petprep_extract_tacs_wf'))

def init_anat_wf():
    from bids import BIDSLayout

    layout = BIDSLayout(args.bids_dir, validate=False)

    anat_wf = Workflow(name='anat_wf', base_dir=args.bids_dir)

    # Define the subjects to iterate over
    subject_list = layout.get(return_type='id', target='subject', suffix='pet')

    # Set up the main workflow to iterate over subjects
    for subject_id in subject_list:
        # For each subject, create a subject-specific workflow
        subject_wf = init_single_subject_anat_wf(subject_id)
        anat_wf.add_nodes([subject_wf])

    return anat_wf

def init_single_subject_anat_wf(subject_id):
    from bids import BIDSLayout

    layout = BIDSLayout(args.bids_dir, validate=False)

    # Create a new workflow for this specific subject
    subject_wf = Workflow(name=f'subject_{subject_id}_wf', base_dir=args.bids_dir)

    templates = {'fs_subject_dir': 'derivatives/freesurfer'}

    selectfiles = Node(SelectFiles(templates,
                                   base_directory=args.bids_dir),
    
                       name="select_files")
    
    datasink = Node(DataSink(base_directory = args.bids_dir,
                                container = os.path.join(args.bids_dir,'anat_wf')),
                    name = 'datasink')
    
    if args.gtm is True:
        gtmseg = Node(GTMSeg(subject_id = f'sub-{subject_id}', 
                            out_file = 'space-T1w_desc-gtmseg_dseg.nii.gz',
                            xcerseg = True),
                    name = 'gtmseg')
        
        subject_wf.connect([(selectfiles, gtmseg, [('fs_subject_dir', 'subjects_dir')]),
                            (gtmseg, datasink, [('out_file', 'datasink.@gtmseg_file')])
                            ])

    if args.brainstem is True:
        segment_bs = Node(SegmentBS(subject_id = f'sub-{subject_id}'),
                                name = 'segment_bs')
        
        subject_wf.connect([(selectfiles, segment_bs, [('fs_subject_dir', 'subjects_dir')])
                            ])
        
    if args.thalamicNuclei is True:
        segment_th = Node(SegmentThalamicNuclei(subject_id = f'sub-{subject_id}'),
                            name = 'segment_th')
            
        subject_wf.connect([(selectfiles, segment_th, [('fs_subject_dir', 'subjects_dir')])
                            ])
    
    return subject_wf

def init_petprep_extract_tacs_wf():
    from bids import BIDSLayout

    layout = BIDSLayout(args.bids_dir, validate=False)

    petprep_extract_tacs_wf = Workflow(name='petprep_extract_tacs_wf', base_dir=args.bids_dir)
    petprep_extract_tacs_wf.config['execution']['remove_unnecessary_outputs'] = 'false'

    # Define the subjects to iterate over
    subject_list = layout.get(return_type='id', target='subject', suffix='pet')

    # Set up the main workflow to iterate over subjects
    for subject_id in subject_list:
        # For each subject, create a subject-specific workflow
        subject_wf = init_single_subject_wf(subject_id)
        petprep_extract_tacs_wf.add_nodes([subject_wf])

    return petprep_extract_tacs_wf


def init_single_subject_wf(subject_id):
    from bids import BIDSLayout

    layout = BIDSLayout(args.bids_dir, validate=False)

    # Create a new workflow for this specific subject
    subject_wf = Workflow(name=f'subject_{subject_id}_wf', base_dir=args.bids_dir)
    subject_wf.config['execution']['remove_unnecessary_outputs'] = 'false'

    subject_data = collect_data(layout,
                            participant_label=subject_id)[0]['pet']

    # This function will strip the extension(s) from a filename
    def strip_extensions(filename):
        while os.path.splitext(filename)[1]:
            filename = os.path.splitext(filename)[0]
        return filename

    # Use os.path.basename to get the last part of the path and then remove the extensions
    cleaned_subject_data = [strip_extensions(os.path.basename(path)) for path in subject_data]

    inputs = Node(IdentityInterface(fields=['pet_file']), name='inputs')
    inputs.iterables = ('pet_file', cleaned_subject_data)

    sessions = layout.get_sessions(subject=subject_id)

    templates = {'pet_file': 's*/pet/*{pet_file}.[n]*' if not sessions else 's*/s*/pet/*{pet_file}.[n]*',
                 'json_file': 's*/pet/*{pet_file}.json' if not sessions else 's*/s*/pet/*{pet_file}.json',
                 'brainmask_file': f'derivatives/freesurfer/sub-{subject_id}/mri/brainmask.mgz',
                 'gtm_file': f'derivatives/freesurfer/sub-{subject_id}/mri/gtmseg.mgz',
                 'bs_labels_voxel': f'derivatives/freesurfer/sub-{subject_id}/mri/brainstemSsLabels.v13.FSvoxelSpace.mgz',
                 'thalamic_labels_voxel': f'derivatives/freesurfer/sub-{subject_id}/mri/ThalamicNuclei.v13.T1.FSvoxelSpace.mgz',
                 'fs_subject_dir': 'derivatives/freesurfer'}

    selectfiles = Node(SelectFiles(templates,
                                   base_directory=args.bids_dir),
                       name="select_files")

    # Define nodes for extraction of tacs

    coreg_pet_to_t1w = Node(MRICoreg(out_lta_file = 'from-pet_to-t1w_reg.lta'),
                       name = 'coreg_pet_to_t1w')
    
    create_time_weighted_average = Node(Function(input_names = ['pet_file', 'json_file'],
                                            output_names = ['out_file'],
                                            function = create_weighted_average_pet),
                                   name = 'create_weighted_average_pet')

    move_pet_to_anat = Node(ApplyVolTransform(transformed_file = 'space-T1w_pet.nii.gz'),
                            name = 'move_pet_to_anat')
    
    move_twa_to_anat = Node(ApplyVolTransform(transformed_file = 'space-T1w_desc-twa_pet.nii.gz'),
                            name = 'move_twa_to_anat')
    
    convert_brainmask = Node(MRIConvert(out_file = 'space-T1w_desc-brain_mask.nii.gz'),
                             name = 'convert_brainmask')
    
    plot_registration = Node(Function(input_names = ['fixed_image', 'moving_image'],
                             output_names = ['out_file'],
                             function = plot_reg),
                        name = 'plot_reg')
    
    datasink = Node(DataSink(base_directory = args.bids_dir,
                                container = os.path.join(args.bids_dir,'extract_tacs_pet_wf')),
                    name = 'datasink')

    subject_wf.connect([(inputs, selectfiles, [('pet_file', 'pet_file')]),
                        (selectfiles, create_time_weighted_average, [('pet_file', 'pet_file')]),
                        (selectfiles, create_time_weighted_average, [('json_file', 'json_file')]),
                        (selectfiles, coreg_pet_to_t1w, [('brainmask_file', 'reference_file')]),
                        (create_time_weighted_average, coreg_pet_to_t1w, [('out_file', 'source_file')]),
                        (coreg_pet_to_t1w, move_pet_to_anat, [('out_lta_file', 'lta_file')]),
                        (selectfiles, move_pet_to_anat, [('brainmask_file', 'target_file')]),
                        (selectfiles, move_pet_to_anat, [('pet_file', 'source_file')]),
                        #(move_pet_to_anat, datasink, [('transformed_file', 'datasink.@transformed_file')]),
                        (coreg_pet_to_t1w, datasink, [('out_lta_file', 'datasink.@out_lta_file')]),
                        (create_time_weighted_average, move_twa_to_anat, [('out_file', 'source_file')]),
                        (selectfiles, move_twa_to_anat, [('brainmask_file', 'target_file')]),
                        (coreg_pet_to_t1w, move_twa_to_anat, [('out_lta_file', 'lta_file')]),
                        (move_twa_to_anat, datasink, [('transformed_file', 'datasink.@transformed_twa_file')]),
                        (selectfiles, convert_brainmask, [('brainmask_file', 'in_file')]),
                        (convert_brainmask, datasink, [('out_file', 'datasink.@brainmask_file')]),
                        (convert_brainmask, plot_registration, [('out_file', 'fixed_image')]),
                        (move_twa_to_anat, plot_registration, [('transformed_file', 'moving_image')]),
                        (plot_registration, datasink, [('out_file', 'datasink.@plot_reg')])
                        ])
    
    if args.gtm is True:
        
            gtmpvc = Node(GTMPVC(default_seg_merge = True,
                                auto_mask = (1,0.1),
                                no_pvc = True,
                                pvc_dir = 'nopvc',
                                no_rescale = True),
                        name = 'gtmpvc')
            
            create_gtmseg_tacs = Node(Function(input_names = ['in_file', 'json_file', 'gtm_stats'],
                                                output_names = ['out_file'],
                                                function = gtm_to_tacs),
                                    name = 'create_gtmseg_tacs')
            
            create_gtmseg_stats = Node(Function(input_names = ['gtm_stats'],
                                                output_names = ['out_file'],
                                                function = gtm_stats_to_stats),
                                    name = 'create_gtmseg_stats')
            
            create_gtmseg_dsegtsv = Node(Function(input_names = ['gtm_stats'],
                                                    output_names = ['out_file'],
                                                    function = gtm_to_dsegtsv),
                                            name = 'create_gtmseg_dsegtsv')
            
            convert_gtmseg_file = Node(MRIConvert(out_file = 'desc-gtmseg_dseg.nii.gz'),
                                    name = 'convert_gtmseg_file')
            
            subject_wf.connect([(selectfiles, gtmpvc, [('pet_file', 'in_file')]),
                            (selectfiles, gtmpvc, [('gtm_file', 'segmentation')]),
                            (coreg_pet_to_t1w, gtmpvc, [('out_lta_file', 'reg_file')]),
                            (gtmpvc, create_gtmseg_tacs, [('nopvc_file', 'in_file')]),
                            (gtmpvc, create_gtmseg_tacs, [('gtm_stats', 'gtm_stats')]),
                            (selectfiles, create_gtmseg_tacs, [('json_file', 'json_file')]),
                            (create_gtmseg_tacs, datasink, [('out_file', 'datasink.@gtmseg_tacs')]),
                            (gtmpvc, create_gtmseg_stats, [('gtm_stats', 'gtm_stats')]),
                            (create_gtmseg_stats, datasink, [('out_file', 'datasink.@gtmseg_stats')]),
                            (selectfiles, convert_gtmseg_file, [('gtm_file', 'in_file')]),
                            (convert_gtmseg_file, datasink, [('out_file', 'datasink.@gtmseg_file')]),
                            (gtmpvc, create_gtmseg_dsegtsv, [('gtm_stats', 'gtm_stats')]),
                            (create_gtmseg_dsegtsv, datasink, [('out_file', 'datasink.@gtmseg_dsegtsv')])
                            ])
            
    if args.brainstem is True:
            segment_bs = Node(SegmentBS(subject_id = f'sub-{subject_id}'),
                                name = 'segment_bs')
            
            segstats_bs = Node(SegStats(exclude_id = 0,
                                        default_color_table = True,
                                        avgwf_txt_file = 'desc-brainstem_tacs.txt',
                                        ctab_out_file = 'desc-brainstem_dseg.ctab',
                                        summary_file = 'desc-brainstem_stats.txt'),
                                name = 'segstats_bs')
            
            create_bs_tacs = Node(Function(input_names = ['avgwf_file', 'ctab_file', 'json_file'],
                                            output_names = ['out_file'],
                                            function = avgwf_to_tacs),
                                    name = 'create_bs_tacs')
            
            create_bs_stats = Node(Function(input_names = ['summary_file'],
                                            output_names = ['out_file'],
                                            function = summary_to_stats),
                                    name = 'create_bs_stats')
            
            create_bs_dsegtsv = Node(Function(input_names = ['ctab_file'],
                                            output_names = ['out_file'],
                                            function = ctab_to_dsegtsv),
                                        name = 'create_bs_dsegtsv')
            
            convert_bs_seg_file = Node(MRIConvert(out_file = 'desc-brainstem_dseg.nii.gz'),
                                    name = 'convert_bs_seg_file')
            
            subject_wf.connect([(selectfiles, segstats_bs, [('bs_labels_voxel', 'segmentation_file')]),
                            (move_pet_to_anat, segstats_bs, [('transformed_file', 'in_file')]),
                            (segstats_bs, create_bs_tacs, [('avgwf_txt_file', 'avgwf_file'),
                                                            ('ctab_out_file', 'ctab_file')]),
                            (selectfiles, create_bs_tacs, [('json_file', 'json_file')]),
                            (segstats_bs, create_bs_stats, [('summary_file', 'summary_file')]),
                            (segstats_bs, create_bs_dsegtsv, [('ctab_out_file', 'ctab_file')]),
                            (selectfiles, convert_bs_seg_file, [('bs_labels_voxel', 'in_file')]),
                            (create_bs_tacs, datasink, [('out_file', 'datasink')]),
                            (create_bs_stats, datasink, [('out_file', 'datasink.@bs_stats')]),
                            (create_bs_dsegtsv, datasink, [('out_file', 'datasink.@bs_dseg')]),
                            (convert_bs_seg_file, datasink, [('out_file', 'datasink.@bs_segmentation_file')])
                            ])
            
    if args.thalamicNuclei is True:            
            segstats_th = Node(SegStats(exclude_id = 0,
                                        default_color_table = True,
                                        avgwf_txt_file = 'desc-thalamus_tacs.txt',
                                        ctab_out_file = 'desc-thalamus_dseg.ctab',
                                        summary_file = 'desc-thalamus_stats.txt'),
                                name = 'segstats_th')
            
            create_th_tacs = Node(Function(input_names = ['avgwf_file', 'ctab_file', 'json_file'],
                                            output_names = ['out_file'],
                                            function = avgwf_to_tacs),
                                    name = 'create_th_tacs')
            
            create_th_stats = Node(Function(input_names = ['summary_file'],
                                            output_names = ['out_file'],
                                            function = summary_to_stats),
                                    name = 'create_th_stats')
            
            create_th_dsegtsv = Node(Function(input_names = ['ctab_file'],
                                            output_names = ['out_file'],
                                            function = ctab_to_dsegtsv),
                                        name = 'create_th_dsegtsv')
            
            convert_th_seg_file = Node(MRIConvert(out_file = 'desc-thalamus_dseg.nii.gz'),
                                    name = 'convert_th_seg_file')
            
            subject_wf.connect([(selectfiles, segstats_th, [('thalamic_labels_voxel', 'segmentation_file')]),
                            (move_pet_to_anat, segstats_th, [('transformed_file', 'in_file')]),
                            (segstats_th, create_th_tacs, [('avgwf_txt_file', 'avgwf_file'),
                                                            ('ctab_out_file', 'ctab_file')]),
                            (selectfiles, create_th_tacs, [('json_file', 'json_file')]),
                            (segstats_th, create_th_stats, [('summary_file', 'summary_file')]),
                            (segstats_th, create_th_dsegtsv, [('ctab_out_file', 'ctab_file')]),
                            (selectfiles, convert_th_seg_file, [('thalamic_labels_voxel', 'in_file')]),
                            (create_th_tacs, datasink, [('out_file', 'datasink.@th_tacs')]),
                            (create_th_stats, datasink, [('out_file', 'datasink.@th_stats')]),
                            (create_th_dsegtsv, datasink, [('out_file', 'datasink.@th_dseg')]),
                            (convert_th_seg_file, datasink, [('out_file', 'datasink.@th_segmentation_file')])
                            ])
            
    return subject_wf

def add_sub(subject_id):
    return 'sub-' + subject_id

if __name__ == '__main__': 
    parser = argparse.ArgumentParser(description='BIDS App for PETPrep extract time activity curves (TACs) workflow')
    parser.add_argument('--bids_dir', required=True,  help='The directory with the input dataset '
                    'formatted according to the BIDS standard.')
    parser.add_argument('--output_dir', required=False, help='The directory where the output files '
                    'should be stored. If you are running group level analysis '
                    'this folder should be prepopulated with the results of the'
                    'participant level analysis.')
    parser.add_argument('--analysis_level', default='participant', help='Level of the analysis that will be performed. '
                    'Multiple participant level analyses can be run independently '
                    '(in parallel) using the same output_dir.',
                    choices=['participant', 'group'])
    parser.add_argument('--participant_label', help='The label(s) of the participant(s) that should be analyzed. The label '
                   'corresponds to sub-<participant_label> from the BIDS spec '
                   '(so it does not include "sub-"). If this parameter is not '
                   'provided all subjects should be analyzed. Multiple '
                   'participants can be specified with a space separated list.',
                   nargs="+", default=None)
    parser.add_argument('--n_procs', help='Number of processors to use when running the workflow', default=2)
    parser.add_argument('--gtm', help='Extract time activity curves from the geometric transfer matrix segmentation (gtmseg)', action='store_true')
    parser.add_argument('--brainstem', help='Extract time activity curves from the brainstem', action='store_true')
    parser.add_argument('--thalamicNuclei', help='Extract time activity curves from the thalamic nuclei', action='store_true')
    parser.add_argument('--hippocampusAmygdala', help='Extract time activity curves from the hippocampus and amygdala', action='store_true')
    parser.add_argument('--wm', help='Extract time activity curves from the white matter', action='store_true')
    parser.add_argument('--raphe', help='Extract time activity curves from the raphe nuclei', action='store_true')
    parser.add_argument('--limbic', help='Extract time activity curves from the limbic system', action='store_true')
    parser.add_argument('--petprep_hmc', help='Use outputs from petprep_hmc as input to workflow', action='store_true')
    parser.add_argument('--skip_bids_validator', help='Whether or not to perform BIDS dataset validation',
                   action='store_true')
    parser.add_argument('-v', '--version', action='version',
                    version='PETPrep extract time activity curves BIDS-App version {}'.format(__version__))
    
    args = parser.parse_args() 
    
    main(args)
