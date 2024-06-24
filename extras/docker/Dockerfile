FROM python:3.9
LABEL MAINTANER="Clayton Boucher <clayton.boucher@campana.com>"

ARG branch=develop

# Get our webdirect application from bitbucket
ADD repo-key /
RUN \
  chmod 600 /repo-key && \
  echo "IdentityFile /repo-key" >> /etc/ssh/ssh_config && \
  echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config && \
  git clone git@bitbucket.org:tdevwebdirect/webdirect.git -b $branch

WORKDIR webdirect
RUN chmod 666 webdirect.py
RUN git rev-parse --short $branch >> build.hash

# Update Python Requirements
# Make sure pip & pipenv is up to date first
RUN python -m pip install -U pip && \
  pip install -U pipenv && \
  pip install pipenv && \ 
  python -m pip cache purge && \
  pipenv install --system

CMD ["./webdirect.py"]
ENTRYPOINT ["python"]