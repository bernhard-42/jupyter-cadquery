FROM continuumio/miniconda3:4.8.2

RUN adduser --disabled-password --gecos "Default user" --uid 1000 cq && \
    apt-get update -y && \
    apt-get install --no-install-recommends -y libgl1-mesa-glx libglu1-mesa && \
    apt-get clean

COPY environment.yml labextensions.txt /tmp/

# To streamline the upload uild one layer that has all fixed parts
RUN grep -v jupyter_cadquery /tmp/environment.yml > /tmp/environment-common.yml  && \
    conda env create -f /tmp/environment-common.yml -n cq && \
    conda install -n cq -y nodejs && \
    conda clean --all && \
    find / -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

# And just add jupyter-cadquery on top
RUN conda env update -f /tmp/environment.yml -n cq && \
    conda run -n cq jupyter labextension install --no-build $(cat /tmp/labextensions.txt) && \
    conda run -n cq jupyter lab build --dev-build=True --minimize=False && \
    conda clean --all && \
    conda run -n cq jupyter lab clean && \
    find / -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

VOLUME /home/cq/
WORKDIR /home/cq
EXPOSE 8888

ADD --chown=cq:cq examples /home/cq

USER cq

CMD bash -l -c "source /opt/conda/bin/activate cq && jupyter lab --ip=0.0.0.0 --no-browser --NotebookApp.token='' --NotebookApp.allow_origin='*'"
