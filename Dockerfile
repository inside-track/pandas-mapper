FROM python:3.6-slim

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
