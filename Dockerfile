# If you need a slim version, use "alpine" base instead of trixie (Debian)
#FROM python:3.12-alpine AS base-image
FROM ubuntu:24.04 AS base-image

# Install packages

#RUN apk add --no-cache bash vim nano libstdc++ libgomp
RUN apt-get update
RUN apt-get dist-upgrade -y
RUN apt-get install -y bash vim nano libgomp1 adduser git openssl make software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update

# Install Python 3.12
RUN apt-get install -y python3.12-full python3.12-dev

# Switch to Bash
SHELL ["/bin/bash", "-c"]

# Delete the build-in user - not needed in alpine images
RUN userdel -r ubuntu

# Create student user
ARG GNAME=student
ARG GID=1000
ARG UNAME=student
ARG UID=1000
ARG UHOME=/home/student
ENV HOME=${UHOME}
RUN set -o errexit -o nounset
RUN addgroup --gid ${GID} "${GNAME}"
RUN adduser --home "${UHOME}" --disabled-password --uid ${UID} --ingroup "${GNAME}" "${UNAME}"
WORKDIR ${UHOME}

# Remove unnecessary sotware
RUN apt-get purge -y adduser software-properties-common
RUN apt-get autoremove -y

FROM base-image AS venv-image


# Install build essentials, to correctly build python deps
# We install it only for this stage, so we create a lighter docker image for executing
#RUN apk add --no-cache alpine-sdk
RUN apt-get update
RUN apt-get install -y build-essential cmake linux-headers-generic

# Create python virtual environment
WORKDIR ${UHOME}
RUN python3.12 -m venv simulaqron-venv
# We have to "manually" activate the virtual environment
ENV PATH="${UHOME}/simulaqron-venv/bin:$PATH"

# Install SimulaQron
# Option 1: Install from the wheel file
# Copy the simulaqron wheel into the container
COPY dist/*.whl ${UHOME}
RUN pip install *.whl
RUN rm *.whl

# Install extra packages that need build-essential
RUN pip install "qutip<5.0.0"
RUN pip install "setuptools<81" pybind11
RUN pip install "git+https://github.com/ProjectQ-Framework/ProjectQ.git@v0.8.0" --no-build-isolation

# Option 2: (Recommended for release) Install from PyPI
#RUN pip install "simulaqron[opt]>=4.0.1"

FROM base-image AS run-image

# Copy installed python packages from previous image
COPY --from=venv-image --chown=${UNAME} ${UHOME}/simulaqron-venv "${UHOME}/.local"
# Since these files come from a python virtual environment
# we need to fix some absolute paths
WORKDIR ${UHOME}/.local/bin
RUN sed -i "s|${UHOME}/simulaqron-venv/|${UHOME}/.local/|g" *
# Activate the "virtual environment" we just copied
ENV PATH="${UHOME}/.local/bin:${UHOME}/.local:$PATH"

# Configure libgomp to use a single thread to avoid deadlocks in simulaqron
ENV OMP_NUM_THREADS=1

# Switch to user student
USER student
WORKDIR ${UHOME}
RUN echo 'export PS1="\[\e]0;\u@\h: \w\a\]${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "' >> ~/.bashrc

CMD bash
