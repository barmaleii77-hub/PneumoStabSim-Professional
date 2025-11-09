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

# X11 + OpenGL/Vulkan headless stack
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates pkg-config build-essential \
    xvfb xauth dbus-x11 \
    mesa-utils mesa-utils-extra \
    libgl1 libgl1-mesa-dri libgl1-mesa-glx libglu1-mesa libglu1-mesa-dev \
    libegl1 libegl1-mesa libegl1-mesa-dev libgles2-mesa libgles2-mesa-dev \
    libosmesa6 libosmesa6-dev libgbm1 libdrm2 \
    libx11-6 libxext6 libxrender1 libxi6 libxfixes3 libxrandr2 libxcursor1 libxinerama1 libxdamage1 \
    libxcb1 libx11-xcb1 libxkbcommon0 libxkbcommon-x11-0 libxcb-xinerama0 \
    libxcb-keysyms1 libxcb-image0 libxcb-icccm4 libxcb-render-util0 libxcb-xfixes0 libxcb-shape0 libxcb-randr0 libxcb-glx0 \
    libvulkan1 mesa-vulkan-drivers vulkan-tools \
    && rm -rf /var/lib/apt/lists/*

# Trust the egress proxy certificate so that Python tooling (aqt/requests)
# can download Qt payloads during image build.
ARG INSTALL_PROXY_CERT=false
RUN if [ "$INSTALL_PROXY_CERT" = "true" ]; then \
        cp config/certs/envoy-mitmproxy-ca-cert.crt /usr/local/share/ca-certificates/ && \
        update-ca-certificates; \
    fi

# Python tooling
RUN pipx ensurepath || true
RUN python -m pip install --no-cache-dir -U pip wheel setuptools \
    aqtinstall ruff mypy pytest pytest-xdist pytest-cov

# Qt 6.10.0 with Quick 3D & tools (qmllint, qsb)
ARG AQT_BASE=https://download.qt.io/online/qtsdkrepository/linux_x64/desktop
ENV QT_VER=6.10.0 QT_ROOT=/opt/Qt AQT_BASE=${AQT_BASE}
# Qt 6.10+ repositories require the repository root so that aqt can discover
# the Updates.xml metadata for each version. Point to the desktop root rather
# than the nested qt6_<version> directory and fail fast if the install payload
# is missing.
RUN python -m aqt install-qt linux desktop ${QT_VER} gcc_64 \
    -b ${AQT_BASE} \
    -m qtquick3d qtshadertools qtimageformats -O ${QT_ROOT} \
    && test -d ${QT_ROOT}/${QT_VER}/gcc_64
ENV QT_HOME=${QT_ROOT}/${QT_VER}/gcc_64
ENV PATH=${QT_HOME}/bin:${PATH}

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
