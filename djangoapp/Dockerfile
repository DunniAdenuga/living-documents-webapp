# start from an official image
FROM python:3.6

RUN pip install -U nltk

# location of source code
RUN mkdir -p /opt/services/djangoapp/
WORKDIR /opt/services/djangoapp/

# install dependencies
# we use --system flag because we don't need an extra virtualenv
COPY requirements.txt /opt/services/djangoapp/
RUN pip install -r requirements.txt
RUN python -m nltk.downloader stopwords
RUN python -m nltk.downloader punkt

# update pip
RUN pip install --upgrade pip

# install pytorch - no CUDA version (for MAC, Linux and Windows)
# The following one command is for MAC
# RUN pip3 install torch torchvision
# The following two commands are for Linux
# RUN pip3 install https://download.pytorch.org/whl/cpu/torch-1.1.0-cp36-cp36m-linux_x86_64.whl
# RUN pip3 install https://download.pytorch.org/whl/cpu/torchvision-0.3.0-cp36-cp36m-linux_x86_64.whl
# RUN pip install torch==1.8.0+cpu torchvision==0.9.0+cpu torchaudio==0.8.0 -f https://download.pytorch.org/whl/torch_stable.html
RUN pip install torch==1.2.0+cpu torchvision==0.4.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
# The following two commands are for Windows
#RUN pip3 install https://download.pytorch.org/whl/cpu/torch-1.1.0-cp36-cp36m-win_amd64.whl
#RUN pip3 install https://download.pytorch.org/whl/cpu/torchvision-0.3.0-cp36-cp36m-win_amd64.whl

# install cytoolz
RUN pip install cytoolz

# for pdf extractor
RUN pip install PyPDF2
RUN pip install textract


RUN pip install PyPDF2
RUN pip install textract

# install summa (https://github.com/summanlp/textrank)
RUN pip install summa

# install pytorch-transformers
RUN pip install pytorch-transformers

# install tensorboardX
RUN pip install tensorboardX

# install gdown
RUN pip install gdown

# install pyrouge
RUN pip install pyrouge

# install transformers
# RUN pip install tqdm boto3 requests regex sentencepiece sacremoses
RUN pip install transformers

# install openai
RUN pip install openai

# copy project code
COPY . /opt/services/djangoapp/
RUN python manage.py collectstatic --no-input

# install gurobi
ENV GUROBI_HOME /opt/services/gurobi801/linux64
ENV GRB_LICENSE_FILE /opt/services/djangoapp/config/gurobi/gurobi.lic
ENV PATH "${PATH}:${GUROBI_HOME}/bin"
ENV LD_LIBRARY_PATH "${LD_LIBRARY_PATH}:${GUROBI_HOME}/lib"
WORKDIR /opt/services/
RUN wget -q https://packages.gurobi.com/8.0/gurobi8.0.1_linux64.tar.gz && \
    tar -xf gurobi8.0.1_linux64.tar.gz && \
    cd /opt/services/gurobi801/linux64 && \
    python setup.py install

WORKDIR /opt/services/djangoapp/

# the run command when starting container
CMD ["gunicorn", "--timeout", "9999", "--keep-alive", "9999", "--worker-connections", "1024", "--bind", ":8000", "living_documents_server.wsgi:application"]
