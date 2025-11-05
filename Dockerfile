# syntax=docker/dockerfile:1.7
ARG PY_VERSION=3.13
FROM mcr.microsoft.com/devcontainers/python:${PY_VERSION}-bookworm

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]

# X11 + OpenGL/Vulkan headless stack
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates pkg-config build-essential \
    xvfb xauth dbus-x11 \
    mesa-utils libgl1-mesa-dri libglu1-mesa \
    libx11-6 libxext6 libxrender1 libxi6 libxfixes3 libxrandr2 libxcursor1 libxinerama1 libxdamage1 \
    libxcb1 libx11-xcb1 libxkbcommon0 libxkbcommon-x11-0 \
    libxcb-keysyms1 libxcb-image0 libxcb-icccm4 libxcb-render-util0 libxcb-xfixes0 libxcb-shape0 libxcb-randr0 libxcb-glx0 \
    libvulkan1 mesa-vulkan-drivers vulkan-tools \
    && rm -rf /var/lib/apt/lists/*

# Python tooling
RUN pipx ensurepath || true
RUN python -m pip install --no-cache-dir -U pip wheel setuptools \
    aqtinstall ruff mypy pytest pytest-xdist pytest-cov

# Qt installation with module availability checks
ARG QT_VERSIONS="6.10.0,6.9.0,6.8.2"
ENV QT_ROOT=/opt/Qt \
    QT_ARCH=gcc_64 \
    QT_VERSIONS=${QT_VERSIONS}


# Workdir
WORKDIR /workdir
COPY . /workdir

# Install Qt after sources are available so the helper script can run
RUN python scripts/install_qt.py

ENV QT_HOME=${QT_ROOT}/current/${QT_ARCH}
ENV PATH=${QT_HOME}/bin:${PATH}

# Helper scripts
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/xvfb_wrapper.sh /usr/local/bin/xvfb_wrapper.sh
RUN chmod +x /usr/local/bin/*.sh

# Optional tools for logs/shader sanity
RUN mkdir -p /workdir/tools /workdir/reports
COPY tools/shader_sanity.py tools/collect_logs.py scripts/install_deps.py scripts/run_all.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/run_all.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
