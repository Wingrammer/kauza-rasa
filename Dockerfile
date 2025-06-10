# The default Docker image
ARG IMAGE_BASE_NAME
ARG BASE_IMAGE_HASH
ARG BASE_BUILDER_IMAGE_HASH
ARG KAUZA_DIALOG_TOKEN

FROM ${IMAGE_BASE_NAME}:base-builder-${BASE_BUILDER_IMAGE_HASH} as builder

# 1. Installation de Git
RUN apt-get update && apt-get install -y git

# 2. Configuration sécurisée de Git
RUN git config --global url."https://api:${KAUZA_DIALOG_TOKEN}@github.com/".insteadOf "https://github.com/"

# 3. Commande de clonage corrigée
RUN git clone --depth 1 --recurse-submodules \
    https://api:${KAUZA_DIALOG_TOKEN}@github.com/Wingrammer/kauza-dialogue.git /build

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

# # init submodule
# RUN git submodule sync && \
#     git submodule update --init --recursive --depth=1 || \
#     { echo "Échec des sous-modules"; git submodule status; exit 1; }

# Initialise submodules if needed
# RUN git submodule update --init --recursive

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