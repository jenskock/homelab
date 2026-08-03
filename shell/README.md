# Remote Shell

Browser terminal at `shell.jenskock.de`.
ttyd on `127.0.0.1:7681` with HTTP basic auth.

## Services

| Service | Build | Role |
| --- | --- | --- |
| `shell-sshd` | [`./sshd`](sshd/) | Landing shell (pubkey SSH) |
| `ttyd` | [`./ttyd`](ttyd/) | Browser ↔ PTY; SSH into `shell-sshd` via tmux |

## Volumes

| Volume | Mount | Purpose |
| --- | --- | --- |
| `shell_ssh` | `/home/jens/.ssh` | Shared keypair / authorized_keys |
| `shell_tmux` | `/home/jens/tmux` | Persistent tmux sessions |

## Setup

```bash
cp env.example /opt/shell/.env
chmod 600 /opt/shell/.env
```

Portainer → Stacks → Add stack → Compose path `shell/docker-compose.yml`
(builds required).

cloudflared on the same host needs a public hostname pointing at
`http://localhost:7681`.
