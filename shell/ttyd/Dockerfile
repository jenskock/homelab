FROM tsl0922/ttyd:latest

USER root

RUN apt-get update \
  && apt-get install -y --no-install-recommends openssh-client tmux wget ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && (getent group jens >/dev/null || groupadd -g 1000 jens) \
  && (getent passwd jens >/dev/null || useradd -u 1000 -g jens -ms /bin/bash -d /home/jens jens) \
  && mkdir -p /home/jens/.ssh /home/jens/tmux \
  && chown -R jens:jens /home/jens

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY shell-session.sh /usr/local/bin/shell-session.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh /usr/local/bin/shell-session.sh

USER jens
WORKDIR /home/jens
EXPOSE 7681
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
