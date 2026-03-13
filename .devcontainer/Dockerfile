FROM node:20-bookworm

ARG TZ
ENV TZ="$TZ"

ARG CLAUDE_CODE_VERSION=latest
ARG CODEX_VERSION=latest
ARG GIT_DELTA_VERSION=0.18.2
ARG ZSH_IN_DOCKER_VERSION=1.2.0
ARG USERNAME=node

ENV PYTHONUNBUFFERED=1

# --------------------------------------------------------------------
# Base packages
# --------------------------------------------------------------------

RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    less \
    git \
    procps \
    sudo \
    fzf \
    zsh \
    man-db \
    unzip \
    gnupg \
    iptables \
    ipset \
    iproute2 \
    dnsutils \
    jq \
    nano \
    vim \
    wget \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev; \
  ln -s /usr/bin/python3 /usr/bin/python; \
  apt-get clean; \
  rm -rf /var/lib/apt/lists/*

# --------------------------------------------------------------------
# npm global folder
# --------------------------------------------------------------------

RUN mkdir -p /usr/local/share/npm-global/lib/node_modules \
    /usr/local/share/npm-global/bin && \
    chown -R node:node /usr/local/share/npm-global

# --------------------------------------------------------------------
# command history
# --------------------------------------------------------------------

RUN mkdir -p /commandhistory && \
    touch /commandhistory/.bash_history && \
    chown -R $USERNAME /commandhistory

ENV DEVCONTAINER=true

# --------------------------------------------------------------------
# workspace folders
# --------------------------------------------------------------------

RUN mkdir -p /workspace \
    /home/node/.claude \
    /home/node/.codex && \
    chown -R node:node /workspace \
    /home/node/.claude \
    /home/node/.codex

WORKDIR /workspace

# --------------------------------------------------------------------
# install git-delta
# --------------------------------------------------------------------

RUN set -eux; \
  ARCH="$(dpkg --print-architecture)"; \
  wget -O /tmp/git-delta.deb \
    "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"; \
  dpkg -i /tmp/git-delta.deb; \
  rm /tmp/git-delta.deb

# --------------------------------------------------------------------
# switch to node user
# --------------------------------------------------------------------

USER node

ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin
ENV SHELL=/bin/zsh
ENV EDITOR=nano
ENV VISUAL=nano

# --------------------------------------------------------------------
# zsh setup
# --------------------------------------------------------------------

RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
  -p git \
  -p fzf \
  -a "source /usr/share/doc/fzf/examples/key-bindings.zsh" \
  -a "source /usr/share/doc/fzf/examples/completion.zsh" \
  -a "export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  -x

# --------------------------------------------------------------------
# install AI CLIs
# --------------------------------------------------------------------

RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION} \
  && npm install -g @openai/codex@${CODEX_VERSION}

# --------------------------------------------------------------------
# firewall script
# --------------------------------------------------------------------

COPY init-firewall.sh /usr/local/bin/

USER root

RUN chmod +x /usr/local/bin/init-firewall.sh && \
  echo "node ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/node-firewall && \
  chmod 0440 /etc/sudoers.d/node-firewall

USER node