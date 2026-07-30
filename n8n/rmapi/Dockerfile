# ddvk/rmapi (juruen/rmapi archived). Assets: rmapi-linux-{amd64,arm64}.tar.gz
# amd64 release is glibc-linked → need libc6-compat on Alpine.
FROM alpine:3.21

ARG TARGETARCH
ARG RMAPI_VERSION=v0.0.34

RUN test -n "$TARGETARCH" \
  && apk add --no-cache ca-certificates curl libc6-compat \
  && curl -fsSL -o /tmp/rmapi.tgz \
    "https://github.com/ddvk/rmapi/releases/download/${RMAPI_VERSION}/rmapi-linux-${TARGETARCH}.tar.gz" \
  && tar -xzf /tmp/rmapi.tgz -C /usr/local/bin rmapi \
  && chmod 755 /usr/local/bin/rmapi \
  && rm -f /tmp/rmapi.tgz \
  && rmapi version \
  && apk del curl

RUN addgroup -g 1000 node \
  && adduser -D -u 1000 -G node node \
  && mkdir -p /data/outbox /data/done /data/failed /home/node/.config/rmapi \
  && chown -R node:node /data /home/node

COPY entrypoint.sh /usr/local/bin/rmapi-watch
RUN chmod 755 /usr/local/bin/rmapi-watch

USER node
WORKDIR /home/node

ENV RMAPI_CONFIG=/home/node/.config/rmapi/rmapi.conf
ENV STAGING_ROOT=/data

ENTRYPOINT ["/usr/local/bin/rmapi-watch"]
