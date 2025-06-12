# The default Docker image
ARG IMAGE_BASE_NAME
ARG BASE_IMAGE_HASH
ARG BASE_BUILDER_IMAGE_HASH
ARG KAUZA_DIALOG_TOKEN

FROM ${IMAGE_BASE_NAME}:base-builder-${BASE_BUILDER_IMAGE_HASH} as builder

# # 1. Installation de Git
# RUN apt-get update && apt-get install -y git

# # 2. Configuration sécurisée de Git
# RUN git config --global url."https://api:${KAUZA_DIALOG_TOKEN}@github.com/".insteadOf "https://github.com/"

# # 3. Commande de clonage corrigée
# RUN git clone --depth 1 --recurse-submodules \
#     https://api:${KAUZA_DIALOG_TOKEN}@github.com/Wingrammer/kauza-dialogue.git /build

COPY . /build/

WORKDIR /build

# # Installer git
# RUN apt-get update && \
#     apt-get install -y git && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# # Config git 
# RUN git config --global url."https://oauth2:${KAUZA_DIALOG_TOKEN}@github.com".insteadOf "https://github.com" && \
#     git config --global advice.detachedHead false

# # Cloner le dépôt principal avec ses sous-modules
# RUN git clone --depth 1 --recurse-submodules \
#     https://oauth2:${KAUZA_DIALOG_TOKEN}@github.com/Wingrammer/kauza-dialogue.git /build || \
#     { echo "Échec du clonage principal"; exit 1; }

# WORKDIR /build


# install dependencies
# RUN python -m venv /opt/venv && \
#   . /opt/venv/bin/activate && \
#   pip install --no-cache-dir -U "pip==22.*" -U "wheel>0.38.0" && \
#   poetry install --no-dev --no-root --no-interaction && \
#   pip install -r requirements.txt&& \
#   poetry build -f wheel -n && \
#   pip install --no-deps dist/*.whl && \
#   rm -rf dist *.egg-info

RUN python -m venv /opt/venv \
  && . /opt/venv/bin/activate \
  && pip install --no-cache-dir -U "pip==22.*" \
  && pip install --no-cache-dir -U "wheel>0.38.0"

# Separate poetry install
RUN . /opt/venv/bin/activate \
  && poetry install --only main --no-root --no-interaction

# Check if requirements.txt install is necessary
RUN . /opt/venv/bin/activate \
  && pip install -r requirements.txt

# Build wheel file with poetry and install it
# RUN . /opt/venv/bin/activate \
#   && poetry build -f wheel -n \
#   && pip install --no-deps dist/*.whl \
#   && rm -rf dist *.egg-info

RUN . /opt/venv/bin/activate && poetry build -f wheel -n
RUN . /opt/venv/bin/activate && pip install --no-deps dist/*.whl
RUN rm -rf dist *.egg-info

# RUN /opt/venv/bin/poetry build -f wheel -n \
#     && /opt/venv/bin/pip install --no-deps dist/*.whl \
#     && rm -rf dist *.egg-info



# start a new build stage
FROM ${IMAGE_BASE_NAME}:base-${BASE_IMAGE_HASH} as runner

# Install tools for .deb (ar, tar, curl)
USER root
RUN apt-get update && apt-get install -y \
    curl \
    binutils \
    xz-utils \
    zstd \
    && rm -rf /var/lib/apt/lists/*


# Download and extract MongoDB crypt library
WORKDIR /tmp/mongo-lib
RUN curl -O https://repo.mongodb.com/apt/ubuntu/dists/jammy/mongodb-enterprise/8.0/multiverse/binary-amd64/mongodb-enterprise-cryptd_8.0.10_amd64.deb \
 && ar x mongodb-enterprise-cryptd_8.0.10_amd64.deb \
 && mkdir -p extract \
 && for f in data.tar.*; do tar -xf "$f" -C extract; done \
 && find extract -name libmongocrypt.so -exec cp {} /usr/local/lib/mongo_crypt/ \;



# Définir la variable d'environnement
ENV SHARED_LIB_PATH=/usr/local/lib/mongo_crypt/libmongocrypt.so

# copy everything from /opt
COPY --from=builder /opt/venv /opt/venv

# make sure we use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# set HOME environment variable
ENV HOME=/app

# update permissions & change user to not run as root
WORKDIR /app
RUN chgrp -R 0 /app && chmod -R g=u /app && chmod o+wr /app
USER 1001

# create a volume for temporary data
VOLUME /tmp

# change shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# the entry point
EXPOSE 5005
ENTRYPOINT ["rasa"]
CMD ["--help"]