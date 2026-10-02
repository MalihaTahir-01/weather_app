# Weather Backend

Built by **Maliha Tahir** for the PM Accelerator AI Engineer Intern
Technical Assessment #2 (Backend).

**About PM Accelerator:** The Product Manager Accelerator Program is designed
to support PM professionals through every stage of their careers. From
students looking for entry-level jobs to Directors looking to take on a
leadership role, the program has helped hundreds of students fulfill their
career aspirations. Its community is ambitious and committed, and through the
program members learn, hone and develop new PM and leadership skills, giving
them a strong foundation for their future endeavors.
(Industry: E-Learning Providers | Boston, MA | Founded 2020 |
https://www.pmaccelerator.io/)

## What it does

A REST API that takes a location and a date range, validates both, fetches
daily temperatures from a real weather API, and stores the result in a
database. Records can be read, updated, deleted and exported.

## Tech stack

- Python, FastAPI, Uvicorn
- SQLite (built-in `sqlite3` module)
- Nominatim / OpenStreetMap: location validation (zip codes, landmarks,
  towns, cities, GPS coordinates)
- Open-Meteo: historical and forecast temperatures (no API key needed)
- fpdf2: PDF export

## How to run

```bash
git clone <your-repo-url>
cd weather_backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API page. The database
file (`weather.db`) is created automatically on first run.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | App info, author, PM Accelerator description |
| GET | `/locations/resolve?query=` | Check that a location exists |
| POST | `/weather` | **Create**: location + date range, fetch and store temperatures |
| GET | `/weather` | **Read** all records (optional `?location=` filter) |
| GET | `/weather/{id}` | **Read** one record |
| PUT | `/weather/{id}` | **Update** location and/or dates (re-validated, temperatures re-fetched) |
| DELETE | `/weather/{id}` | **Delete** a record |
| GET | `/weather/{id}/extras` | Google Maps link and YouTube results for the location |
| GET | `/export?format=` | Export to `json`, `csv`, `md`, `xml` or `pdf` (optional `record_id`) |

## Validation and error handling

- **Dates:** end date must not be before start date, range is at most 31 days,
  start date not before 1940, end date at most 15 days in the future.
- **Location:** must resolve to a real place, otherwise 404. GPS input like
  `48.8584, 2.2945` is range-checked and reverse-geocoded.
- **External services down:** returns 502 with a clear message instead of
  crashing.
- Invalid formats (for example a non-date string) return 422 automatically.

## Design notes

- Create and Update share one `build_record` function, so updates get exactly
  the same validation as creates.
- Updating a location or date range re-fetches temperatures, so stored data
  never contradicts the stored location and dates.
- Past dates use the Open-Meteo archive API; recent and future dates use the
  forecast API.

## YouTube (optional)

Set `YOUTUBE_API_KEY` as an environment variable to get video results from the
`/extras` endpoint. Without it, the endpoint returns a YouTube search link
instead. Never commit API keys to the repository.

## Limitations

- Temperatures only (max, min, mean in °C), not full weather conditions.
- Location lookup is rate-limited by Nominatim to about one request per second.
- No authentication, since the assessment doesn't require row-level security.