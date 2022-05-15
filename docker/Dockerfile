FROM condaforge/mambaforge:4.12.0-0

RUN adduser --disabled-password --gecos "Default user" --uid 1000 cq && \
    apt-get update -y && \
    apt-get install --no-install-recommends -y libgl1-mesa-glx libglu1-mesa && \
    apt-get clean

RUN mamba create -n cq -y python=3.9 && \
    mamba install -n cq -y -c conda-forge "hdf5=1.10.6=nompi_h6a2412b_1114" && \
    mamba install -n cq -y -c conda-forge "OCP=7.5.3" "vtk=9.0.1" "matplotlib=3.5" && \
    mamba clean --all && \
    find / -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

RUN mamba install -n cq -y -c conda-forge -c cadquery cadquery=master && \
    mamba clean --all && \
    find / -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

RUN . "/opt/conda/etc/profile.d/conda.sh" && conda activate cq && \
    pip install jupyter-cadquery==3.1.0rc4 cadquery-massembly~=0.9 jupyterlab~=3.3 voila~=0.3 && \
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
