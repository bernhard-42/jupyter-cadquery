FROM condaforge/mambaforge:4.12.0-0

RUN adduser --disabled-password --gecos "Default user" --uid 1000 cq && \
    apt-get update -y && \
    apt-get install --no-install-recommends -y libgl1-mesa-glx libglu1-mesa && \
    apt-get clean

RUN mamba create -n cq -y python=3.10 && \
    mamba install -n cq -y -c conda-forge -c cadquery OCP=7.6.3 vtk=9.2 matplotlib=3.5 && \
    mamba clean --all && \
    find / -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

RUN mamba install -n cq -y -c conda-forge -c cadquery cadquery=master && \
    mamba clean --all && \
    find / -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

RUN . "/opt/conda/etc/profile.d/conda.sh" && conda activate cq && \
    pip install jupyter-cadquery==3.5.2 cadquery-massembly~=1.0.0 jupyterlab~=3.5 voila~=0.3.5 && \
    find / -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

VOLUME /home/cq/
WORKDIR /home/cq
EXPOSE 8888

USER cq 

ADD --chown=cq:cq examples /home/cq
ADD --chown=cq:cq viewer.ipynb /home/cq
ADD --chown=cq:cq run.sh /tmp
RUN chmod +x /tmp/run.sh

ENTRYPOINT ["/tmp/run.sh"]
