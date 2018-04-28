FROM ubuntu:14.04

# Miniconda (w/ Python 3.6)
RUN apt-get update && apt-get install -y\
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
ENV CONDA_DIR /opt/conda
ENV PATH $CONDA_DIR/bin:$PATH
ENV MINICONDA_VERSION 4.3.21
RUN cd /tmp && \
    mkdir -p $CONDA_DIR && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh && \
    echo "c1c15d3baba15bf50293ae963abef853 *Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh" | md5sum -c - && \
    /bin/bash Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh -f -b -p $CONDA_DIR && \
    rm Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh && \
    $CONDA_DIR/bin/conda config --system --prepend channels conda-forge && \
    $CONDA_DIR/bin/conda config --system --set auto_update_conda false && \
    $CONDA_DIR/bin/conda config --system --set show_channel_urls true && \
    $CONDA_DIR/bin/conda update --all && \
    conda clean -tipsy

# App-specific packages
RUN apt-get update && apt-get install -y \
    bash-completion \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Tini
ARG TINI_VERSION
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

# Conveniences
RUN echo 'source /usr/share/bash-completion/bash_completion' >> /etc/bash.bashrc
RUN echo 'export HISTFILE=$HOME/.bash_history/history' >> $HOME/.bashrc

# App
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN pip install --upgrade pip && rm -rf /root/.cache
RUN pip install pip-tools invoke && rm -rf /root/.cache
RUN pip install -r requirements.txt && rm -rf /root/.cache

# Configure Jupyterlab
ENV PYTHONPATH /app
RUN jupyter serverextension enable --py jupyterlab --sys-prefix
ADD jupyter_notebook_config.py /root/.jupyter/jupyter_notebook_config.py

ENTRYPOINT ["/tini", "--"]
