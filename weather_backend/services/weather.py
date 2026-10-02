from datetime import date, timedelta
import requests

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

MAX_RANGE_DAYS = 31          # longest range a user can request
MAX_FUTURE_DAYS = 15         # forecast data only reaches ~16 days ahead
MAX_PAST_FORECAST_DAYS = 90  # forecast API only keeps ~92 days of past data
ARCHIVE_DELAY_DAYS = 7       # archive data lags a few days behind today


class InvalidDateRangeError(Exception):
    """The date range is incoherent or outside what the API supports."""


class WeatherServiceError(Exception):
    """The weather service could not be reached or returned bad data."""


def validate_date_range(start: date, end: date) -> None:
    today = date.today()

    if end < start:
        raise InvalidDateRangeError("End date cannot be before start date.")
    if start < date(1940, 1, 1):
        raise InvalidDateRangeError("Start date cannot be before 1940-01-01.")
    if end > today + timedelta(days=MAX_FUTURE_DAYS):
        raise InvalidDateRangeError(
            f"End date cannot be more than {MAX_FUTURE_DAYS} days in the future."
        )
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise InvalidDateRangeError(
            f"Date range cannot be longer than {MAX_RANGE_DAYS} days."
        )


def fetch_temperatures(lat: float, lon: float, start: date, end: date) -> list:
    today = date.today()

    # Old dates -> archive API. Recent/future dates -> forecast API.
    if end <= today - timedelta(days=ARCHIVE_DELAY_DAYS):
        url = ARCHIVE_URL
    else:
        if start < today - timedelta(days=MAX_PAST_FORECAST_DAYS):
            raise InvalidDateRangeError(
                "This range mixes very old and very recent dates. "
                "Please split it into two separate requests."
            )
        url = FORECAST_URL

    try:
        response = requests.get(
            url,
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean",
                "timezone": "auto",
            },
            timeout=15,
        )
        response.raise_for_status()
        daily = response.json()["daily"]
    except (requests.RequestException, KeyError, ValueError) as e:
        raise WeatherServiceError(f"Weather service error: {e}")

    # Turn Open-Meteo's parallel lists into one dict per day
    return [
        {
            "date": d,
            "temp_max_c": mx,
            "temp_min_c": mn,
            "temp_mean_c": avg,
        }
        for d, mx, mn, avg in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            daily["temperature_2m_mean"],
        )
    ]