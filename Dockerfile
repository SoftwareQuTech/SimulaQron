## Dockerfile
# This container provides a complete run-time environment for SimulaQron.
#
## Build:
# From inside the top-level SimulaQron directory run
#
#     docker build -t <image_name> .
#
# where you should replace <image_name> with the name you want to give to the
# docker image.
#
## Run:
# To start the container and enter the shell prompt inside, run
#
#     docker run -it <image_name>
#
# This will start a docker container with SimulaQron inside the
# /workspace/SimulaQron directory (this default can be changed, by changing the
# WORKSPACE variable in this file). Note that this is only a COPY of the
# SimulaQron directory that was made during the build step so if you make any
# changes on the host system, they will not be reflected in the container until
# you rebuild the image.
#
# However, if you wish, you can mount the host's SimulaQron directory into the
# container rather than using a copy made during the build step, you need to
# explicitly mount it when starting the container, e.g.
#
#     docker run -it -v /path/to/SimulaQron:/workspace/SimulaQron <image_name>
#
# This will mount /path/to/SimulaQron inside the container in
# /workspace/SimulaQron. Note that on Linux systems with SELinux present, the
# mount option has to be `-v /path/to/SimulaQron:/workspace/SimulaQron:z`.
#
## Multiple shells:
# To attach to a running container with a new shell run
#
#     docker exec -it <container_name> bash
#
# where <container_name> is the name of the running container (this is in
# general not the same as the image name). To find what name your container
# has, run `docker ps`.

FROM ubuntu:18.04
LABEL author="Wojciech Kozlowski <w.kozlowski@tudelft.nl>"

# Update docker image
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get upgrade -y

# Install Python 3
RUN apt-get install -y python3 python3-pip python3-tk

# Set a UTF-8 locale - this is needed for some python packages to play nice
RUN apt-get -y install language-pack-en
ENV LANG="en_US.UTF-8"

RUN pip3 install simulaqron
