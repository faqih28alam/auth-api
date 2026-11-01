# Auth API

FastAPI service for registration, login, and admin user management. Accounts have the role `admin` or `user`. Passwords are hashed with Argon2id. Sessions use a short-lived access JWT and a rotating refresh token stored only as a hash in MongoDB.

The first time the API starts against an empty database it creates an admin account:

| Field | Default |
| --- | --- |
| Username | `Admin` |
| Password | `Admin123` |
| Email | `admin@example.com` |

Change that password before anyone else can reach the service. Login accepts either the email or the username, and both are matched without case sensitivity. Registration accepts only email, username, and password, and always creates an active `user`.

## Requirements

- Python 3.12 or newer for a host install
- Docker Engine with the Compose plugin, for MongoDB and for the container workflows

## Configuration

```bash
cp .env.example .env
```

```powershell
Copy-Item .env.example .env
```

`.env.example` is safe to copy for local use. Before a production deploy, set a long random `JWT_SECRET`, replace `MONGO_INITDB_ROOT_PASSWORD` (and the matching password inside `MONGODB_URI`), set `ADMIN_PASSWORD`, and set `CORS_ORIGINS` and `TRUSTED_HOSTS` to the real hostnames. `ENVIRONMENT=production` refuses to start when `JWT_SECRET` is still the example value or shorter than 32 characters. If the admin password is still `Admin123`, the process starts and logs a warning.

Access tokens last 15 minutes. Refresh tokens last 7 days, rotate on every refresh, and are revoked on logout and on password change. A deactivated account fails the next request immediately, because each request loads the user from the database. Logout revokes the refresh token; an access token that was already issued remains valid until it expires unless the account is deactivated.

## Local API on your machine

Use this when you want to run uvicorn on the host and MongoDB in Docker.

### macOS or Linux

Run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
docker compose up -d mongo
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Stop the API with Ctrl+C in that terminal. Stop MongoDB with:

```bash
docker compose stop mongo
```

Update after pulling new code:

```bash
python -m pip install -e ".[dev]"
docker compose up -d mongo
```

Then start uvicorn again.

Clean the checkout and delete the database volume:

```bash
deactivate
rm -rf .venv
docker compose down -v
```

`down -v` removes MongoDB data, including users and refresh tokens.

### Windows PowerShell

Run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
docker compose up -d mongo
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Stop the API with Ctrl+C. Stop MongoDB with:

```powershell
docker compose stop mongo
```

Update after pulling new code:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
docker compose up -d mongo
```

Then start uvicorn again.

Clean the checkout and delete the database volume:

```powershell
Remove-Item -Recurse -Force .venv
docker compose down -v
```

`down -v` removes MongoDB data, including users and refresh tokens.

Interactive API docs are at <http://localhost:8001/docs> while `ENVIRONMENT` is not `production`.

## Local stack in Docker

These commands are the same on macOS, Linux, and Windows. Copy `.env` first. Compose points the API container at the `mongo` service even if `MONGODB_URI` in `.env` uses `localhost`.

Run:

```bash
docker compose up -d --build
```

Stop the containers and keep the database volume:

```bash
docker compose stop
```

Stop and remove the containers, and keep the volume:

```bash
docker compose down
```

Update after code changes:

```bash
docker compose up -d --build
```

Clean containers and delete the database volume:

```bash
docker compose down -v
```

The API listens on port 8001. MongoDB listens on port 27017 so host tools and a host-run uvicorn process can connect.

## Production on a server

Terminate HTTPS in a reverse proxy on the same machine. The production Compose file publishes the API on `127.0.0.1:8001` only, and it does not publish MongoDB. A Caddy site block is enough:

```text
api.example.com {
    reverse_proxy 127.0.0.1:8001
}
```

Set `TRUSTED_HOSTS` to that public hostname and `CORS_ORIGINS` to the browser origin. The app also accepts `localhost` and `127.0.0.1` so the container health check can call the API on the loopback interface. Then:

```bash
cp .env.example .env
```

Edit `.env` before the first start: replace `JWT_SECRET`, `MONGO_INITDB_ROOT_PASSWORD`, the password embedded in `MONGODB_URI`, and `ADMIN_PASSWORD`. Set `CORS_ORIGINS` and `TRUSTED_HOSTS`.

Run:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Stop, and keep the data volume:

```bash
docker compose -f docker-compose.prod.yml stop
```

Remove the containers, and keep the volume:

```bash
docker compose -f docker-compose.prod.yml down
```

Update after pulling new code:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Clean containers and delete the production database volume:

```bash
docker compose -f docker-compose.prod.yml down -v
```

OpenAPI is disabled when `ENVIRONMENT=production`. The production file forces that value.

After the first start, sign in as the seeded admin and change the password:

```bash
curl -s -X POST http://127.0.0.1:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login":"Admin","password":"Admin123"}'
```

```bash
curl -s -X PATCH http://127.0.0.1:8001/api/v1/users/me/password \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password":"Admin123","new_password":"REPLACE_WITH_A_STRONG_PASSWORD1"}'
```

On Windows PowerShell, call `curl.exe` so the `curl` alias is not used.

## API

Public:

- `POST /api/v1/auth/register` with `email`, `username`, and `password`
- `POST /api/v1/auth/login` with `login` (email or username) and `password`
- `POST /api/v1/auth/refresh` with `refresh_token`
- `GET /api/v1/health`

Signed in (`Authorization: Bearer`):

- `POST /api/v1/auth/logout` with `refresh_token`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me/password` with `current_password` and `new_password`

Admin:

- `GET /api/v1/admin/users` with optional `page`, `limit`, `role`, and `search`
- `GET /api/v1/admin/users/stats`
- `GET /api/v1/admin/users/{id}`
- `PATCH /api/v1/admin/users/{id}` with `role` and/or `is_active`
- `DELETE /api/v1/admin/users/{id}`

Usernames are 3–32 characters and may contain letters, digits, and underscores. Passwords are 8–128 characters and need an uppercase letter, a lowercase letter, and a digit. Responses never include password hashes. An admin cannot delete their own account, and the last active admin cannot be demoted, deactivated, or deleted.

Register is limited to 3 requests per minute, login to 5, and refresh to 10, per client address.

## Security

Queries are built inside the repository. Client JSON is validated against a fixed schema and is never used as a MongoDB operator. Search text is escaped before it is placed in a regular expression. The access token algorithm is fixed to HS256. Production also enables a CORS allowlist, trusted hosts, security headers, a 64 KB body limit, and a non-root user in the image. Put TLS in the reverse proxy. The application does not terminate HTTPS.

## Tests

Start MongoDB, then run pytest from the repository root. The default test URI is `mongodb://auth:authpass@localhost:27017/?authSource=admin`. Override it with `TEST_MONGODB_URI` if needed.

```bash
docker compose up -d mongo
python -m pytest
```

```powershell
docker compose up -d mongo
.\.venv\Scripts\python.exe -m pytest
```
