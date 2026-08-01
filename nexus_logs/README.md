# Nexus Logs

A self-hosted, mobile-friendly workflow tracker for an electrician's daily jobs. It imports a Google Maps Timeline export, lets you attach parts-used/comments to each site visit, fills in gaps Google's GPS missed, and exports the combined log to CSV/XLSX for admin.

## Features

- **Timeline import** — upload a `Timeline.json` / `location-history.json` export (Google Maps → Timeline → Settings → Export Timeline data) and it's parsed into a chronological list of visits and drives.
- **Daily/weekly dashboard** — filter by date range, see driving time/distance and time-at-site exactly like the phone's Timeline UI, with an option to hide your home address.
- **Job data entry** — each visit expands into a form for parts used (one per line) and comments/issues, saved permanently against that visit.
- **Add Missing Job** — manually log a site visit the phone's GPS never captured (signal loss, dead battery), with optional estimated driving time, parts and comments — shown alongside imported data everywhere.
- **Export** — combined log (locations, times, driving, parts, comments) to CSV or XLSX.
- **Settings** — default export format, home address to filter from the dashboard.
- **Safe re-imports** — Google only offers a full-history export, not an incremental one, so every import re-submits everything you've ever recorded. Nexus Logs matches visits/drives against what's already stored (Google's own `place_id` + start time, not the full time window) and only refines Google-derived fields on a repeat import — it never creates duplicates and never touches parts/comments/names you've typed in. See `tracker/parsers.py` and `_import_parsed_entries` in `tracker/views.py` for the details, including why nested "sub-visit" segments in the export are intentionally skipped.

## Tech stack

Django 4.2 · SQLite · Tailwind CSS (CDN, no JS build step) · gunicorn + whitenoise · Docker / Docker Compose

## Quick start (Docker — the intended deployment)

```bash
git clone https://github.com/G3rtPB87/G3rtPB87_Dev.git
cd G3rtPB87_Dev/nexus_logs   # adjust if the repo layout differs
cp .env.example .env         # set DJANGO_SECRET_KEY
docker compose up --build -d
```

Open `http://<linux-host-ip>:8000` from your phone or any browser on the same network. SQLite data persists in `./data/` on the host, so `docker compose down` / rebuilds don't lose anything.

To create an admin login for `/admin/` (optional, for browsing raw records):

```bash
docker compose exec web python manage.py createsuperuser
```

## Local development (no Docker)

```bash
cd nexus_logs
pip3 install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
```

Visit `http://127.0.0.1:8000`.

## Configuration

Set via environment variables (see `docker-compose.yml` / `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | *(insecure dev key)* | Set a real random value in production |
| `DJANGO_DEBUG` | `true` | Set `false` in production |
| `DJANGO_ALLOWED_HOSTS` | `*` | Comma-separated hostnames/IPs |
| `DJANGO_TIME_ZONE` | `Africa/Johannesburg` | Used for date-range filtering and display |

App-level preferences (default export format, home address to hide from the dashboard) are set at `/config/` in the UI, stored in the database.

## Project structure

```
nexus_logs/
├── manage.py
├── requirements.txt
├── Dockerfile / docker-compose.yml
├── nexus_logs/              Django project settings, urls, wsgi
└── tracker/                 the app
    ├── models.py              TimelineEntry (visits + drives), AppConfig
    ├── parsers.py             Timeline.json -> structured dicts
    ├── forms.py, views.py, urls.py, admin.py
    └── templates/tracker/     dashboard, upload, manual_entry, config
```

## Data model

Both visits and drives live in one `TimelineEntry` table (`entry_type` distinguishes them), ordered by `start_time`, so the dashboard is a single chronological query rather than a merge of two tables. `source` marks whether a row came from a parsed export (`google`) or was typed in via "Add Missing Job" (`manual`). `parts_used`/`comments` live on the same row as the visit.

## Backing up your data

Everything lives in `data/db.sqlite3` (mounted as a volume in Docker). Back that single file up on whatever schedule you'd back up any local database.
