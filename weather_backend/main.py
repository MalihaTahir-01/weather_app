import json
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel

from database import init_db, get_connection
from services.geocoding import (
    resolve_location,
    LocationNotFoundError,
    GeocodingServiceError,
)
from services.weather import (
    validate_date_range,
    fetch_temperatures,
    InvalidDateRangeError,
    WeatherServiceError,
)
from services.extras import get_extras
from services.export import FORMATS

AUTHOR = "Maliha Tahir"

ABOUT_PMA = (
    "The Product Manager Accelerator Program is designed to support PM "
    "professionals through every stage of their careers. From students "
    "looking for entry-level jobs to Directors looking to take on a "
    "leadership role, the program has helped hundreds of students fulfill "
    "their career aspirations. Its community is ambitious and committed, "
    "and through the program members learn, hone and develop new PM and "
    "leadership skills, giving them a strong foundation for their future "
    "endeavors."
)

PMA_FACTS = (
    "Industry: E-Learning Providers | Headquarters: Boston, MA | "
    "Founded: 2020 | Website: https://www.pmaccelerator.io/"
)

DESCRIPTION = f"""
Built by **{AUTHOR}** for the PM Accelerator AI Engineer Intern
Technical Assessment #2 (Backend).

**About PM Accelerator:** {ABOUT_PMA}

{PMA_FACTS}
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Weather Backend",
    description=DESCRIPTION,
    lifespan=lifespan,
)


class WeatherCreate(BaseModel):
    location: str
    start_date: date
    end_date: date


class WeatherUpdate(BaseModel):
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


def row_to_dict(row) -> dict:
    record = dict(row)
    record["temperature_data"] = json.loads(record["temperature_data"])
    return record


def get_row_or_404(conn, record_id: int):
    row = conn.execute(
        "SELECT * FROM weather_requests WHERE id = ?", (record_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404, detail=f"Record {record_id} not found."
        )
    return row


def build_record(location: str, start: date, end: date) -> dict:
    """Validate dates and location, then fetch temperatures.
    Shared by CREATE and UPDATE so both get the same validation."""
    try:
        validate_date_range(start, end)
    except InvalidDateRangeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        place = resolve_location(location)
    except LocationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GeocodingServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    try:
        temps = fetch_temperatures(
            place["latitude"], place["longitude"], start, end
        )
    except InvalidDateRangeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WeatherServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {"place": place, "temps": temps}


@app.get("/")
def root():
    return {
        "app": "Weather Backend",
        "author": AUTHOR,
        "about_pm_accelerator": ABOUT_PMA,
        "company_facts": PMA_FACTS,
        "docs": "/docs",
    }


@app.get("/locations/resolve")
def resolve(query: str = Query(..., min_length=1)):
    try:
        return resolve_location(query)
    except LocationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GeocodingServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/weather", status_code=201)
def create_weather(payload: WeatherCreate):
    built = build_record(payload.location, payload.start_date, payload.end_date)
    place, temps = built["place"], built["temps"]

    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO weather_requests
            (location_query, resolved_name, country, latitude, longitude,
             start_date, end_date, temperature_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.location,
                place["name"],
                place["country"],
                place["latitude"],
                place["longitude"],
                payload.start_date.isoformat(),
                payload.end_date.isoformat(),
                json.dumps(temps),
                now,
                now,
            ),
        )
        row = get_row_or_404(conn, cursor.lastrowid)

    return row_to_dict(row)


@app.get("/weather")
def list_weather(
    location: Optional[str] = Query(
        None, description="Filter by part of the location name"
    ),
):
    with get_connection() as conn:
        if location:
            like = f"%{location}%"
            rows = conn.execute(
                """
                SELECT * FROM weather_requests
                WHERE location_query LIKE ? OR resolved_name LIKE ?
                ORDER BY id DESC
                """,
                (like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM weather_requests ORDER BY id DESC"
            ).fetchall()

    return [row_to_dict(r) for r in rows]


@app.get("/weather/{record_id}")
def get_weather(record_id: int):
    with get_connection() as conn:
        row = get_row_or_404(conn, record_id)
    return row_to_dict(row)


@app.put("/weather/{record_id}")
def update_weather(record_id: int, payload: WeatherUpdate):
    if (
        payload.location is None
        and payload.start_date is None
        and payload.end_date is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of: location, start_date, end_date.",
        )

    with get_connection() as conn:
        existing = get_row_or_404(conn, record_id)

        new_location = payload.location or existing["location_query"]
        new_start = payload.start_date or date.fromisoformat(
            existing["start_date"]
        )
        new_end = payload.end_date or date.fromisoformat(existing["end_date"])

        built = build_record(new_location, new_start, new_end)
        place, temps = built["place"], built["temps"]

        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            """
            UPDATE weather_requests
            SET location_query = ?, resolved_name = ?, country = ?,
                latitude = ?, longitude = ?, start_date = ?, end_date = ?,
                temperature_data = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                new_location,
                place["name"],
                place["country"],
                place["latitude"],
                place["longitude"],
                new_start.isoformat(),
                new_end.isoformat(),
                json.dumps(temps),
                now,
                record_id,
            ),
        )
        row = get_row_or_404(conn, record_id)

    return row_to_dict(row)


@app.delete("/weather/{record_id}")
def delete_weather(record_id: int):
    with get_connection() as conn:
        get_row_or_404(conn, record_id)
        conn.execute("DELETE FROM weather_requests WHERE id = ?", (record_id,))
    return {"message": f"Record {record_id} deleted."}


@app.get("/weather/{record_id}/extras")
def get_weather_extras(record_id: int):
    with get_connection() as conn:
        row = get_row_or_404(conn, record_id)
    return get_extras(row["resolved_name"], row["latitude"], row["longitude"])


@app.get("/export")
def export_data(
    format: str = Query("json", pattern="^(json|csv|md|xml|pdf)$"),
    record_id: Optional[int] = Query(
        None, description="Export one record, or leave empty for all"
    ),
):
    with get_connection() as conn:
        if record_id is not None:
            rows = [get_row_or_404(conn, record_id)]
        else:
            rows = conn.execute(
                "SELECT * FROM weather_requests ORDER BY id"
            ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No records to export.")

    records = [row_to_dict(r) for r in rows]
    converter, media_type = FORMATS[format]
    return Response(
        content=converter(records),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename=weather_export.{format}"
        },
    )