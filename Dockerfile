# Use the official Python base image for x86_64
FROM --platform=linux/x86_64 python:3.9

# Download QEMU for cross-compilation
ADD https://github.com/multiarch/qemu-user-static/releases/download/v6.1.0-8/qemu-x86_64-static /usr/bin/qemu-x86_64-static
RUN chmod +x /usr/bin/qemu-x86_64-static

# Install required dependencies for FSL and Freesurfer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    git \
    tcsh \
    xfonts-base \
    gfortran \
    libjpeg62 \
    libtiff5-dev \
    libpng-dev \
    unzip \
    libxext6 \
    libx11-6 \
    libxmu6 \
    libglib2.0-0 \
    libxft2 \
    libxrender1 \
    libxt6 \
    ffmpeg \
    libsm6

# Install Freesurfer
ENV FREESURFER_HOME="/opt/freesurfer" \
    PATH="/opt/freesurfer/bin:$PATH" \
    FREESURFER_VERSION=7.4.1 \
    USE_LOCAL_FREESURFER=False

# copy over local freesurfer binaries
RUN mkdir /freesurfer_binaries
COPY freesurfer_binaries/* /freesurfer_binaries/

ARG USE_LOCAL_FREESURFER
RUN echo USE_LOCAL_FREESURFER=${USE_LOCAL_FREESURFER}

RUN if [ "$USE_LOCAL_FREESURFER" = "True" ]; then \
      echo "Using local freesurfer binaries."; \
      tar xzC /opt -f /freesurfer_binaries/freesurfer-linux-centos7_x86_64-${FREESURFER_VERSION}.tar.gz && \
      echo ". /opt/freesurfer/SetUpFreeSurfer.sh" >> ~/.bashrc; \
    fi && \
    if [ "$USE_LOCAL_FREESURFER" = "False" ]; then \
      echo "Using freesurfer binaries from surfer.nmr.mgh.harvard.edu."; \
      curl -L --progress-bar https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/${FREESURFER_VERSION}/freesurfer-linux-centos7_x86_64-${FREESURFER_VERSION}.tar.gz | tar xzC /opt && \
      echo ". /opt/freesurfer/SetUpFreeSurfer.sh" >> ~/.bashrc; \
    fi

RUN rm -rf /freesurfer_binaries

# set bash as default terminal
SHELL ["/bin/bash", "-ce"]

# create directories for mounting input, output and project volumes
RUN mkdir -p /input /output /petprep_extract_tacs

ENV PATH="/root/.local/bin:$PATH"
# setup fs env
ENV PATH=/opt/freesurfer/bin:/opt/freesurfer/fsfast/bin:/opt/freesurfer/tktools:/opt/freesurfer/mni/bin:${PATH} \
    OS=Linux \
    FREESURFER_HOME=/opt/freesurfer \
    FREESURFER=/opt/freesurfer \
    SUBJECTS_DIR=/opt/freesurfer/subjects \
    LOCAL_DIR=/opt/freesurfer/local \
    FSFAST_HOME=/opt/freesurfer/fsfast \
    FMRI_ANALYSIS_DIR=/opt/freesurfer/fsfast \
    FUNCTIONALS_DIR=/opt/freesurfer/sessions \
    FS_OVERRIDE=0 \
    FIX_VERTEX_AREA="" \
    FSF_OUTPUT_FORMAT=nii.gz \
    MINC_BIN_DIR=/opt/freesurfer/mni/bin \
    MINC_LIB_DIR=/opt/freesurfer/mni/lib \
    MNI_DIR=/opt/freesurfer/mni \
    MNI_DATAPATH=/opt/freesurfer/mni/data \
    MNI_PERL5LIB=/opt/freesurfer/mni/share/perl5 \
    PERL5LIB=/opt/freesurfer/mni/share/perl5

RUN /opt/freesurfer/bin/fs_install_mcr R2019b 

# copy the project files
COPY . /petprep_extract_tacs/

# install dependencies
RUN pip3 install --upgrade pip && cd /petprep_extract_tacs && pip3 install -e .

# do a bunch of folder creation before we're not root
RUN mkdir -p /.local/bin && \
    mkdir -p /.cache && \
    mkdir -p /.config/matplotlib && \
    mkdir -p /logs/ && \
    mkdir -p /workdir/ && \
    chmod -R 777 /workdir/ && \
    chmod -R 777 /logs/ && \
    chmod -R 777 /.config && \
    chmod -R 777 /output/ && \
    chmod -R 777 /.cache/ && \
    chmod -R 777 /.local/

COPY docker_own.sh /petprep_extract_tacs/docker_own.sh
COPY nipype.config.docker /petprep_extract_tacs/nipype.config
COPY nipype.config.docker /root/nipype.config
# set the entrypoint to the main executable run.py
WORKDIR "/workdir"
ENTRYPOINT ["python3", "/petprep_extract_tacs/run.py"]
