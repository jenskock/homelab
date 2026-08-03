FROM tsl0922/ttyd:latest

USER root

# ubuntu:24.04 (ttyd base) already has UID/GID 1000 as user "ubuntu".
RUN apt-get update \
  && apt-get install -y --no-install-recommends openssh-client tmux wget ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && groupmod -n jens ubuntu \
  && usermod -l jens -d /home/jens -m ubuntu \
  && mkdir -p /home/jens/.ssh /home/jens/tmux \
  && chown -R jens:jens /home/jens

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY shell-session.sh /usr/local/bin/shell-session.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh /usr/local/bin/shell-session.sh

USER jens
WORKDIR /home/jens
EXPOSE 7681
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
