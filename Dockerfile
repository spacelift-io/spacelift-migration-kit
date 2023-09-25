FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Persist Bash history
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/command-history/.bash_history" \
  && mkdir /command-history \
  && touch /command-history/.bash_history \
  && chown -R vscode /command-history \
  && echo "$SNIPPET" >> "/home/vscode/.bashrc"

# Install dependencies
COPY requirements.txt .
RUN pip install --requirement requirements.txt
