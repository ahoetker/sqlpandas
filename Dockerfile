FROM ubuntu:16.04
WORKDIR /app

# install apt-get and build tools
RUN apt-get update && apt-get install -y \
  curl apt-utils apt-transport-https debconf-utils gcc build-essential g++-5\
  && rm -rf /var/lib/apt/lists/*

# add Microsoft repository for mssql driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

# install mssql driver
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql unixodbc-dev

# instal mssql tools
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y mssql-tools
RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
RUN /bin/bash -c "source ~/.bashrc"

# install python 3 and pip
RUN apt-get update && apt-get install -y \
  python3-pip python3-dev python3-setuptools \
  --no-install-recommends \
  && rm -rf /var/lib/apt/lists/* \
  && ln -s /usr/bin/python3 /usr/local/bin/python \
  && pip3 install -U pip

# configure locale
RUN apt-get update && apt-get install -y locales \
  && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
  && locale-gen

# install pyodbc
RUN pip3 install pyodbc

# install python package requirements
COPY ./requirements.txt /app
RUN pip install -r /app/requirements.txt

RUN mkdir visualizations

COPY ./proof_of_concept.py /app

CMD ["/usr/bin/python3", "-i", "/app/proof_of_concept.py"]
