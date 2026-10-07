# Weather Backend

Made by Maliha Tahir for the PM Accelerator AI Engineer Intern Technical Assessment #2 (Backend).

## About PM Accelerator

The Product Manager Accelerator Program is designed to support PM professionals through every stage of their careers. From students looking for entry-level jobs to Directors looking to take on a leadership role, the program has helped hundreds of students fulfill their career aspirations. Its community is ambitious and committed, and through the program members learn, hone and develop new PM and leadership skills, giving them a strong foundation for their future endeavors.

Industry: E-Learning Providers | Boston, MA | Founded 2020 | https://www.pmaccelerator.io/

## Demo video
https://drive.google.com/file/d/1DvY5EYTpPyWMffoGnFcwQDidp4n5s34d/view?usp=sharing


## What this project does

This is a weather app backend made with FastAPI. The user gives a location and a date range, and the app checks both, gets the daily temperatures from a real weather API and saves them in a database. The saved records can be viewed, updated, deleted and exported. For each record you can also get a Google Maps link and YouTube videos of that place.

## Tools I used

- Python and FastAPI (with Uvicorn to run it)
- SQLite for the database
- Nominatim (OpenStreetMap) to check that a location is real
- Open-Meteo to get the temperatures (no API key needed)
- fpdf2 for the PDF export
- YouTube Data API (optional, needs a key)

## Files

- main.py: all the API endpoints
- database.py: creates the SQLite database and table
- services/geocoding.py: checks the location
- services/weather.py: checks the dates and gets the temperatures
- services/extras.py: Google Maps link and YouTube videos
- services/export.py: exports to JSON, CSV, XML, Markdown and PDF
- requirements.txt: the packages to install

## How to run

You need Python 3.10 or newer.

```
git clone <your-repo-url>
cd weather_backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

On Mac or Linux, use `source .venv/bin/activate` instead of the Activate.ps1 line.

Then open http://127.0.0.1:8000/docs in the browser. You can test every endpoint from that page. The database file (weather.db) is made automatically the first time you run it.

## Endpoints

- GET `/` : app info, my name and the PM Accelerator description
- GET `/locations/resolve?query=` : checks if a location exists
- POST `/weather` : CREATE a record (location + start date + end date)
- GET `/weather` : READ all records, can filter with `?location=`
- GET `/weather/{id}` : READ one record
- PUT `/weather/{id}` : UPDATE the location and/or dates
- DELETE `/weather/{id}` : DELETE a record
- GET `/weather/{id}/extras` : Google Maps link and YouTube videos
- GET `/export?format=` : export as json, csv, md, xml or pdf (add `&record_id=` for one record)

Example for creating a record:

```
{
  "location": "Lahore",
  "start_date": "2026-09-01",
  "end_date": "2026-09-05"
}
```

The location can be a city, town, zip code, landmark or GPS coordinates like `48.8584, 2.2945`.

## Validation and errors

- End date before start date gives a 400 error
- Date range longer than 31 days gives a 400 error
- Start date before 1940 or end date more than 15 days in the future gives a 400 error
- A location that does not exist gives a 404 error
- GPS coordinates outside the valid range give a 404 error
- A record id that does not exist gives a 404 error
- If the weather or location service is down, it gives a 502 error with a message instead of crashing
- Wrong data types (like text in a date field) give a 422 error automatically

## Some things I did

- Create and update use the same function (`build_record`), so updates are checked the same way as new records.
- When a record is updated, the temperatures are fetched again so the saved data always matches the new location and dates.
- Old dates use the Open-Meteo archive API and recent or future dates use the forecast API.
- The CSV export has one row per day so it opens nicely in Excel.

## YouTube key (optional)

To get real YouTube videos, set an environment variable called `YOUTUBE_API_KEY`. Without it, the app just gives a YouTube search link. I did not put my key in the code.

## Limitations

- It only gives temperatures (max, min and mean in °C), not rain, wind, etc.
- Nominatim only allows about one request per second.
- There is no login, because the assessment says row level security is not needed.
- The PDF export can't show non-English characters properly.