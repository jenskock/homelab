#!/bin/sh
set -eu

SSH_DIR=/home/jens/.ssh
KEY="${SSH_DIR}/id_ed25519"

mkdir -p "${SSH_DIR}"
chmod 700 "${SSH_DIR}"

if [ ! -f "${KEY}" ]; then
  ssh-keygen -t ed25519 -N "" -f "${KEY}" -C "shell-stack@ttyd"
fi

if [ ! -f "${SSH_DIR}/authorized_keys" ]; then
  cp "${KEY}.pub" "${SSH_DIR}/authorized_keys"
fi

chmod 600 "${KEY}" "${SSH_DIR}/authorized_keys"
chmod 644 "${KEY}.pub"
chown -R jens:jens "${SSH_DIR}"

if [ ! -f /etc/ssh/ssh_host_ed25519_key ]; then
  ssh-keygen -t ed25519 -N "" -f /etc/ssh/ssh_host_ed25519_key
fi
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
  ssh-keygen -t rsa -b 4096 -N "" -f /etc/ssh/ssh_host_rsa_key
fi

exec /usr/sbin/sshd -D -e -f /etc/ssh/sshd_config
