ARG VARIANT
FROM mcr.microsoft.com/devcontainers/base:$VARIANT

# Ensure proper behavior on errors in pipes
# See https://github.com/hadolint/hadolint/wiki/DL4006
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Persist Poetry cache
ENV POETRY_CACHE_DIR=/poetry-cache
RUN mkdir /poetry-cache \
  && chown vscode /poetry-cache

# Persist pre-commit cache
ENV PRE_COMMIT_HOME=/pre-commit-cache
RUN mkdir /pre-commit-cache \
  && chown vscode /pre-commit-cache

# Persist Bash history
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/command-history/.bash_history" \
  && mkdir /command-history \
  && touch /command-history/.bash_history \
  && chown -R vscode /command-history \
  && echo "$SNIPPET" >> /home/vscode/.bashrc

# Install python dependencies
# hadolint ignore=DL3008
RUN apt-get update \
  && apt-get install --no-install-recommends -y \
  libbz2-dev \
  liblzma-dev \
  libreadline-dev \
  libsqlite3-dev \
  && rm -rf /var/lib/apt/lists/*

# Install Pyenv
ENV PYENV_ROOT=/home/vscode/.pyenv
# hadolint ignore=SC2016
RUN curl https://pyenv.run | bash \
  && echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> /home/vscode/.bashrc \
  && echo 'eval "$(pyenv init -)"' >> /home/vscode/.bashrc

# Install Python
RUN $PYENV_ROOT/bin/pyenv install 3.{10..12}:latest \
  && $PYENV_ROOT/bin/pyenv global 3.{10..12} \
  && chown -R vscode $PYENV_ROOT
