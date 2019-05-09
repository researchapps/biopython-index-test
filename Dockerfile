FROM python:3.7.3-stretch

# docker build -t vanessa/biopython .

RUN mkdir -p /code && \
    mydir=$(mktemp -d) && \
    cd "${mydir}" || exit 1  && \
    git clone https://github.com/TomHarrop/biopython-index-test.git  && \
    cd biopython-index-test || exit 1  && \
    rm r1.fq.gz  && \
    wget -O r1.fq.gz \
        --no-check-certificate \
        https://github.com/TomHarrop/biopython-index-test/raw/master/r1.fq.gz  && \
    gunzip r1.fq.gz && \
    mv r1.fq /r1.fq && \
    /usr/local/bin/pip3 install intermine==1.11.0

ADD index_reads.py /index_reads.py

WORKDIR /code
COPY biopython-1.73-custom/ /code/
RUN ls /code && pip3 install .

ENTRYPOINT ["python3"]
CMD ["/index_reads.py"]
