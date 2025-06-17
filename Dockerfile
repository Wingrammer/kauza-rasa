# The default Docker image
ARG IMAGE_BASE_NAME
ARG BASE_IMAGE_HASH
ARG BASE_BUILDER_IMAGE_HASH
ARG KAUZA_DIALOG_TOKEN
ARG AZURE_TENANT_ID
ARG AZURE_CLIENT_ID
ARG AZURE_CLIENT_SECRET

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

# Installer les dépendances nécessaires
RUN apt-get update && apt-get install -y \
  curl \
  binutils \
  xz-utils \
  zstd \
  && rm -rf /var/lib/apt/lists/*

# Télécharger et extraire mongo_crypt_v1.so depuis le .tgz
WORKDIR /tmp/mongo-lib
RUN curl -O https://downloads.mongodb.com/linux/mongo_crypt_shared_v1-linux-x86_64-enterprise-ubuntu2204-8.0.10.tgz \
  && tar -xzf mongo_crypt_shared_v1-linux-x86_64-enterprise-ubuntu2204-8.0.10.tgz \
  && ls -lR lib \
  && find lib -name mongo_crypt_v1.so \
  && cp -v ./lib/mongo_crypt_v1.so /usr/lib/x86_64-linux-gnu/ \
  && test -f /usr/lib/x86_64-linux-gnu/mongo_crypt_v1.so \
  && rm -rf /tmp/mongo-lib

# Définir le chemin vers la librairie dynamique
ENV SHARED_LIB_PATH=/usr/lib/x86_64-linux-gnu/mongo_crypt_v1.so


# copy everything from /opt
COPY --from=builder /opt/venv /opt/venv

# make sure we use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# set HOME environment variable
ENV HOME=/app

ENV AZURE_TENANT_ID=${AZURE_TENANT_ID}
ENV AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
ENV AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}

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