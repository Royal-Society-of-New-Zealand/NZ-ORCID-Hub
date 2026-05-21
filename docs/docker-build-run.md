# Docker Build & Run Guide

This guide covers two scenarios:
- **Local testing** — build images from source on your dev machine
- **Live deployment** — update the running instances on the VM

PowerShell equivalents are provided at the end of each section for Windows users.

---

## Local Testing

### Prerequisites

Before running the app locally you need a PostgreSQL database and Redis instance. There are two ways to provide them:

**Option A — docker-compose standalone profile (recommended for local dev)**
The simplest approach. The `standalone` profile starts containerised PostgreSQL and Redis alongside the app. No separate setup required — just run:
```bash
docker compose --profile standalone up -d
```
See Section 2 for full details.

**Option B — docker-compose without the standalone profile**
Use this when you already have PostgreSQL and Redis running elsewhere (e.g. installed locally or on a remote host). Set `DATABASE_URL` and `RQ_REDIS_URL` in `.env` to point at your existing instances, then run:
```bash
docker compose up -d
```
The `db` and `redis` services will not start — the app connects to whatever your env vars point at.

**Option C — manual `docker run` (advanced)**
For running a single image directly without Compose. Requires a shared Docker network and a temporary PostgreSQL container so the app can reach the database by hostname. Also requires a local `.keys` directory — `run-app` generates a self-signed SSL certificate here on first start.

**bash / zsh**
```bash
# Shared network so app can reach postgres by hostname
docker network create orcid-test-net

# Temporary PostgreSQL
docker run --rm -d --name orcid-test-pg \
  --network orcid-test-net \
  -e POSTGRES_PASSWORD=test \
  postgres:15.2

# Wait until PostgreSQL is ready before starting the app
docker run --rm --network orcid-test-net postgres:15.2 \
  pg_isready -h orcid-test-pg -U postgres

# Create the keys directory for SSL cert generation
mkdir -p /tmp/orcid-test-keys
```

**PowerShell**
```powershell
# Shared network so app can reach postgres by hostname
docker network create orcid-test-net

# Temporary PostgreSQL
docker run --rm -d --name orcid-test-pg `
  --network orcid-test-net `
  -e POSTGRES_PASSWORD=test `
  postgres:15.2

# Wait until PostgreSQL is ready before starting the app
docker run --rm --network orcid-test-net postgres:15.2 `
  pg_isready -h orcid-test-pg -U postgres

# Create the keys directory for SSL cert generation
New-Item -ItemType Directory -Force -Path C:\tmp\orcid-test-keys
```

---

### 1. Production Image (`Dockerfile`)

**bash / zsh**
```bash
# Build
docker build --target orcidhub -t orcidhub/app .
# or
make build

# Run
docker run --rm -p 8080:80 -p 8443:443 \
  --network orcid-test-net \
  -e DATABASE_URL="postgresql://postgres:test@orcid-test-pg:5432/postgres" \
  -v /tmp/orcid-test-keys:/.keys \
  -v $(pwd):/src \
  -v $(pwd):/var/www/orcidhub \
  orcidhub/app

# Test
curl -I http://localhost:8080      # expect 302 redirect to HTTPS
curl -sk https://localhost:8443    # expect NZ ORCID Hub HTML
```

**PowerShell**
```powershell
# Build
docker build --target orcidhub -t orcidhub/app .

# Run
docker run --rm -p 8080:80 -p 8443:443 `
  --network orcid-test-net `
  -e DATABASE_URL="postgresql://postgres:test@orcid-test-pg:5432/postgres" `
  -v C:\tmp\orcid-test-keys:/.keys `
  -v ${PWD}:/src `
  -v ${PWD}:/var/www/orcidhub `
  orcidhub/app

# Test
curl -I http://localhost:8080
curl --insecure https://localhost:8443
```

---

### 2. Dev Image via docker-compose (`Dockerfile.dev`)

`docker-compose.yml` uses `image: orcidhub/app-dev:latest` — the same image family as the live
deployments. You must build it locally first before running Compose.

> **Note:** `make` is not available on Windows by default. Use the manual PowerShell commands instead.

**bash / zsh**
```bash
# Build (production base first, then dev layer — make build-dev does both)
make build-dev

# Run (full stack — includes containerised postgres and redis via standalone profile)
docker compose --profile standalone up -d
docker compose ps
curl -I http://localhost

# Tear down (must use same profile to stop db and redis)
docker compose --profile standalone down
```

**PowerShell**
```powershell
# Build (no make on Windows — run steps manually)
docker build --target orcidhub -t orcidhub/app .
docker build -f Dockerfile.dev -t orcidhub/app-dev .

# Run (full stack)
docker compose --profile standalone up -d
docker compose ps
curl -I http://localhost

# Tear down
docker compose --profile standalone down
```

#### Tuakiri SSO (local testing)

To test Tuakiri login locally, set `EXTERNAL_SP` in `.env` before starting the stack:

```
EXTERNAL_SP=https://test.orcidhub.org.nz/saml/SP
```

Then access the app at **`https://localhost`** (not any other hostname). The test server's CSRF
domains include `localhost`, which allows the SSO redirect-back to work.

---

### 3. Test Image (`Dockerfile.test`)

The test image is a standalone Rocky Linux 9 build used for running the automated test suite in CI. It does **not** layer on the production image and is tagged `orcidhub/app-test`.

**bash / zsh**
```bash
# Build
docker build -f Dockerfile.test -t orcidhub/app-test .
# or
make build-test

# Run the test suite
docker run --rm \
  --network orcid-test-net \
  -e DATABASE_URL="postgresql://postgres:test@orcid-test-pg:5432/postgres" \
  -v $(pwd):/src \
  orcidhub/app-test \
  bash -c "cd /src && ./pytest.sh"

# Run a specific test file
docker run --rm \
  --network orcid-test-net \
  -e DATABASE_URL="postgresql://postgres:test@orcid-test-pg:5432/postgres" \
  -v $(pwd):/src \
  orcidhub/app-test \
  bash -c "cd /src && pytest tests/test_models.py -v"
```

> Note: The test suite uses SQLite in-memory by default (`pytest.sh` sets `DATABASE_URL=sqlite:///:memory:`), so the PostgreSQL container and network are only needed if you override `DATABASE_URL` to point at a real Postgres instance.

**PowerShell**
```powershell
# Build
docker build -f Dockerfile.test -t orcidhub/app-test .

# Run the test suite (uses SQLite in-memory — no Postgres container required)
docker run --rm `
  -v ${PWD}:/src `
  orcidhub/app-test `
  bash -c "cd /src && ./pytest.sh"

# Run a specific test file
docker run --rm `
  -v ${PWD}:/src `
  orcidhub/app-test `
  bash -c "cd /src && pytest tests/test_models.py -v"
```

---

### Fresh Rebuilds (no cache)

By default Docker caches each build layer. If you need a clean rebuild — e.g. after changing
`requirements.txt`, pulling updated base images, or debugging a build issue — add `--no-cache`:

**bash / zsh**
```bash
# Production image
docker build --no-cache --target orcidhub -t orcidhub/app .

# Dev image (rebuild both layers)
docker build --no-cache --target orcidhub -t orcidhub/app .
docker build --no-cache -f Dockerfile.dev -t orcidhub/app-dev .

# Test image
docker build --no-cache -f Dockerfile.test -t orcidhub/app-test .
```

**PowerShell**
```powershell
# Production image
docker build --no-cache --target orcidhub -t orcidhub/app .

# Dev image (rebuild both layers)
docker build --no-cache --target orcidhub -t orcidhub/app .
docker build --no-cache -f Dockerfile.dev -t orcidhub/app-dev .

# Test image
docker build --no-cache -f Dockerfile.test -t orcidhub/app-test .
```

> Also pull fresh base images before a no-cache build if you want to pick up OS/package updates:
> ```bash
> docker pull rockylinux:9
> docker pull postgres:15.2
> docker pull redis:7
> ```

---

### Cleanup

**bash / zsh**
```bash
docker stop orcid-test-pg
docker network rm orcid-test-net
docker compose --profile standalone down
rm -rf /tmp/orcid-test-keys
```

**PowerShell**
```powershell
docker stop orcid-test-pg
docker network rm orcid-test-net
docker compose --profile standalone down
Remove-Item -Recurse -Force C:\tmp\orcid-test-keys
```

---

## Live Deployment (VM)

The three live instances (orcidhub, test, dev) each have their own directory on the VM containing a `docker-compose.yml` and supporting files. They all use pre-built images pulled from Docker Hub — they do not build from source.

### Deploying a New Image Version

**Step 1 — Build, tag, and push from your dev machine:**

**bash / zsh**
```bash
# Build all images
make build       # orcidhub/app
make build-dev   # orcidhub/app-dev (builds app first automatically)

# Tag with version
make tag         # orcidhub/app:8.0
make tag-dev     # orcidhub/app-dev:8.0

# Push to Docker Hub
make push        # pushes app:8.0, app-dev:8.0, app:latest, app-dev:latest
# or just dev image
make push-dev
```

**PowerShell** (no `make` — run steps manually)
```powershell
$VERSION = "8.0"

# Build
docker build --target orcidhub -t orcidhub/app .
docker build -f Dockerfile.dev -t orcidhub/app-dev .

# Tag
docker tag orcidhub/app "orcidhub/app:$VERSION"
docker tag orcidhub/app-dev "orcidhub/app-dev:$VERSION"

# Push
docker push "orcidhub/app:$VERSION"
docker push "orcidhub/app-dev:$VERSION"
docker push orcidhub/app:latest
docker push orcidhub/app-dev:latest
```

**Step 2 — On the VM, for each instance directory:**

```bash
# Pull the new image
docker compose pull

# Restart with the new image
docker compose up -d
```

> **Note — image choice per instance:**
> All three instances (`orcidhub/`, `test/`, `dev/`) currently appear to use `orcidhub/app-dev` and share
> the same `docker-compose.yml` structure on the VM.

---

## Key Differences: Local vs Live

| | Local Testing | Live VM |
|---|---|---|
| **Image source** | Built locally via `make build-dev`, referenced as `orcidhub/app-dev:latest` | Pulled from Docker Hub via `docker compose pull` (`orcidhub/app-dev:8.0`) |
| **PostgreSQL** | Temporary Docker container | Runs on the VM host, mounted via `/var/run/postgresql` |
| **Redis** | Docker container (via docker-compose) or none | Runs on the VM host, referenced by `RQ_REDIS_URL` |
| **SSL certs** | Auto-generated self-signed in `/tmp/orcid-test-keys` | Real certs in `.keys/` directory in each instance folder |
| **`app.conf`** | Minimal (HTTP only) from `conf/app.conf` in repo | Full production config mounted from `./app.conf` in instance folder |
| **Source code** | Mounted from repo (`-v $(pwd):/src`) | Mounted from instance directory on VM |
| **`DATABASE_URL`** | TCP connection with explicit port (required by `run-app` parser) | Socket path (`postgresql://orcidhub@/orcidhub?host=/run/postgresql`) or omitted to use socket auto-detection |
| **Ports** | `8080:80` (avoids conflicts) | `80:80`, `443:443` |
| **Restart policy** | None (`--rm`) | `restart: always` |

## Image Summary

| Image | Dockerfile | `make` target | Purpose |
|---|---|---|---|
| `orcidhub/app` | `Dockerfile` | `make build` | Production — Apache + mod_wsgi + Shibboleth |
| `orcidhub/app-dev` | `Dockerfile.dev` | `make build-dev` | Dev — layers hot-reload / debug tools on top of prod |
| `orcidhub/app-test` | `Dockerfile.test` | `make build-test` | CI test runner — standalone Rocky Linux 9 build |

### Important Local Testing Gotchas

- **`DATABASE_URL` must include an explicit port** (e.g. `@host:5432/db`). The `run-app` script parses the host and port with a regex — a URL without a port will cause it to fall back to `db:5432` which won't resolve locally.
- **`/.keys` must be a mounted directory**, even if empty. `run-app` tries to write generated certs there and will error if the path doesn't exist. The generated certs are reused on subsequent runs.
- **`/src` must be mounted** so that `flask initdb` (run on every startup) can find the app code.
- The repo's `docker-compose.yml` is for local use only and is not used on the VM.
- **Windows path syntax**: Use `C:\tmp\orcid-test-keys` for volume mounts in PowerShell. Docker Desktop on Windows also accepts `/c/tmp/orcid-test-keys` (Git Bash style). Backtick (`` ` ``) is the PowerShell line-continuation character — not `\`.
