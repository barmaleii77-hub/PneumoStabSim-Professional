# syntax=docker/dockerfile:1.7
ARG PY_VERSION=3.13
FROM mcr.microsoft.com/devcontainers/python:${PY_VERSION}-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV QT_QPA_PLATFORM=offscreen \
    QT_QUICK_BACKEND=software \
    LIBGL_ALWAYS_SOFTWARE=1 \
    MESA_GL_VERSION_OVERRIDE=4.1 \
    MESA_GLSL_VERSION_OVERRIDE=410
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]

ARG INSTALL_PROXY_CERT=true

COPY config/certs/envoy-mitmproxy-ca-cert.crt /tmp/envoy-mitmproxy-ca-cert.crt
COPY config/aqt-docker.ini /tmp/aqt-docker.ini

# X11 + OpenGL/Vulkan headless stack
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates pkg-config build-essential \
    xvfb xauth dbus-x11 \
    mesa-utils mesa-utils-extra \
    libgl1 libgl1-mesa-dri libglu1-mesa libglu1-mesa-dev \
    libegl1 libegl-dev libgles2 libgles-dev \
    libosmesa6 libosmesa6-dev libgbm1 libdrm2 \
    libx11-6 libxext6 libxrender1 libxi6 libxfixes3 libxrandr2 libxcursor1 libxinerama1 libxdamage1 \
    libxcb1 libx11-xcb1 libxkbcommon0 libxkbcommon-x11-0 libxcb-xinerama0 \
    libxcb-keysyms1 libxcb-image0 libxcb-icccm4 libxcb-render-util0 libxcb-xfixes0 libxcb-shape0 libxcb-randr0 libxcb-glx0 \
    libvulkan1 mesa-vulkan-drivers vulkan-tools \
    && rm -rf /var/lib/apt/lists/*

# Trust the egress proxy certificate so that Python tooling (aqt/requests)
# can download Qt payloads during image build. The certificate is present in
# the repository and copied into the build context so that we can opt-in during
# image builds that sit behind the envoy MITM proxy.
RUN if [ "$INSTALL_PROXY_CERT" = "true" ]; then \
        cp /tmp/envoy-mitmproxy-ca-cert.crt /usr/local/share/ca-certificates/ && \
        update-ca-certificates; \
    fi && rm -f /tmp/envoy-mitmproxy-ca-cert.crt

# Provide a stable aqt configuration that pins the base URL and avoids
# untrusted mirrors when resolving metadata.
ENV AQT_CONFIG=/tmp/aqt-docker.ini

# Python tooling
RUN pipx ensurepath || true
RUN python -m pip install --no-cache-dir -U pip wheel setuptools \
    aqtinstall ruff mypy pytest pytest-xdist pytest-cov

# Qt 6.9.x with Quick 3D & tooling support (qmllint, qsb)
ARG AQT_BASE=https://download.qt.io/online/qtsdkrepository/linux_x64/desktop
ARG QT_VERSION=6.9.3
ENV QT_VERSIONS=${QT_VERSION} QT_ROOT=/opt/Qt QT_ARCH=gcc_64 AQT_BASE=${AQT_BASE}

# Workdir
WORKDIR /workdir
COPY . /workdir

# Use the repository-managed aqt configuration once the sources are present.
ENV AQT_CONFIG=/workdir/config/aqt-docker.ini

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
