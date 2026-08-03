# Remote Shell

Browser terminal at `shell.jenskock.de`.
ttyd with HTTP basic auth; reachable by cloudflared on the `homelab` network.

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

cloudflared public hostname service: `http://shell-ttyd:7681`
(not `localhost` — cloudflared runs in Docker).
