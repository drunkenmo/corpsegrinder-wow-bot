ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.21
FROM ${BUILD_FROM}
ARG BUILD_VERSION=1.0.5
ARG BUILD_ARCH=amd64
LABEL io.hass.version="${BUILD_VERSION}" io.hass.type="app" io.hass.arch="${BUILD_ARCH}"
RUN apk add --no-cache python3 py3-pip && python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install --no-cache-dir discord.py==2.6.4
COPY bot.py /app/bot.py
COPY community_features.py /app/community_features.py
COPY run.sh /run.sh
RUN chmod +x /run.sh
CMD ["/run.sh"]
