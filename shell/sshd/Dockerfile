FROM alpine:3.21

RUN apk add --no-cache openssh openssh-server openssh-client \
  && addgroup -g 1000 jens \
  && adduser -D -u 1000 -G jens -s /bin/sh -h /home/jens jens \
  && passwd -u jens \
  && mkdir -p /home/jens/.ssh /var/run/sshd \
  && chown -R jens:jens /home/jens

COPY sshd_config /etc/ssh/sshd_config
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh \
  && chmod 644 /etc/ssh/sshd_config

EXPOSE 22
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
