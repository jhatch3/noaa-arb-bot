import requests
from datetime import datetime
from dateutil import tz

# Timezone object for Pacific Time (handles PST/PDT automatically)
pst_timezone = tz.gettz("America/Los_Angeles")

headers = {
    "User-Agent": "(yourapp.example, you@example.com)",
    "Accept": "application/geo+json"
}

lat, lon = 44.0521, -123.0868  # Eugene, OR

# Step 1: Get point metadata
p = requests.get(f"https://api.weather.gov/points/{lat},{lon}", headers=headers, timeout=20)
p.raise_for_status()
points = p.json()

# Step 2: Get hourly forecast URL
hourly_url = points["properties"]["forecastHourly"]

# Step 3: Pull hourly forecast data
fh = requests.get(hourly_url, headers=headers, timeout=20)
fh.raise_for_status()
data = fh.json()
import requests
from datetime import datetime
from dateutil import tz

# -------------------------
# CONFIG
# -------------------------
PST_TZ = tz.gettz("America/Los_Angeles")

headers = {
    "User-Agent": "(yourapp.example, you@example.com)",
    "Accept": "application/geo+json"
}

lat, lon = 44.0521, -123.0868  # Eugene, OR


# -------------------------
# NOAA / NWS REQUESTS
# -------------------------
p = requests.get(f"https://api.weather.gov/points/{lat},{lon}", headers=headers, timeout=20)
p.raise_for_status()
points = p.json()

hourly_url = points["properties"]["forecastHourly"]

fh = requests.get(hourly_url, headers=headers, timeout=20)
fh.raise_for_status()
data = fh.json()


# -------------------------
# FORMAT HELPERS
# -------------------------
def _fmt_qv(value):
    """
    Formats NWS values that may be:
    - plain numbers/strings
    - QuantitativeValue dicts like {"value": 12, "unitCode": "..."}
    """
    if isinstance(value, dict):
        v = value.get("value")
        if v is None:
            return "N/A"
        if isinstance(v, float):
            return f"{v:.1f}"
        return str(v)
    if value is None:
        return "N/A"
    return str(value)


def _fmt_percent(obj):
    """Formats NWS percentage fields (often {'value': X})"""
    if isinstance(obj, dict):
        v = obj.get("value")
        if v is None:
            return "N/A"
        return f"{int(round(v))}%"
    if obj is None:
        return "N/A"
    try:
        return f"{int(round(float(obj)))}%"
    except Exception:
        return str(obj)


def _to_local_str(iso_str, tz_name="America/Los_Angeles"):
    target_tz = tz.gettz(tz_name)
    dt_obj = datetime.fromisoformat(iso_str)
    local_dt = dt_obj.astimezone(target_tz)
    return local_dt.strftime("%a %m/%d %I:%M:%S %p %Z")  # 25 chars for PST


def _truncate(text, width):
    text = (str(text) if text is not None else "").replace("\n", " ").strip()
    if len(text) <= width:
        return text
    if width <= 3:
        return "." * width
    return text[: width - 3] + "..."


def _hr_line(width):
    return "+" + "-" * (width - 2) + "+"


def _center_line(text, width):
    text = text[: width - 4]
    pad = width - 2 - len(text)
    left = pad // 2
    right = pad - left
    return "|" + " " * left + text + " " * right + "|"


def _left_line(text, width):
    text = text[: width - 4]
    return "| " + text + " " * (width - 3 - len(text)) + "|"


def print_forecast_cli(data, city_name="Eugene, OR", tz_name="America/Los_Angeles", limit=25):
    """
    Pretty CLI formatter for NWS forecastHourly JSON (data = fh.json()).
    """
    props = data.get("properties", {})
    periods = props.get("periods", []) or []

    total = len(periods)
    shown = min(limit, total)

    # Header metadata
    updated = props.get("updateTime") or props.get("generatedAt") or "N/A"
    try:
        updated_local = _to_local_str(updated, tz_name) if updated != "N/A" else "N/A"
    except Exception:
        updated_local = str(updated)

    # ---- Column widths (FIXED) ----
    # Increased Local Time so "Sat 02/21 04:00:00 PM PST" fits without clipping
    col_idx = 4
    col_time = 26
    col_temp = 8
    col_wind = 14
    col_rh = 6
    col_pop = 6
    col_fcst = 42

    # Build table header first so we can match banner width exactly
    header = (
        f"| {'#':<{col_idx}}"
        f"| {'Local Time':<{col_time}}"
        f"| {'Temp':<{col_temp}}"
        f"| {'Wind':<{col_wind}}"
        f"| {'RH':<{col_rh}}"
        f"| {'PoP':<{col_pop}}"
        f"| {'Short Forecast':<{col_fcst}}|"
    )

    divider = (
        f"|{'-' * (col_idx + 1)}"
        f"|{'-' * (col_time + 1)}"
        f"|{'-' * (col_temp + 1)}"
        f"|{'-' * (col_wind + 1)}"
        f"|{'-' * (col_rh + 1)}"
        f"|{'-' * (col_pop + 1)}"
        f"|{'-' * (col_fcst + 1)}|"
    )

    # Match banner width to the table width (or longer if metadata lines need it)
    info_lines = [
        f" Location : {city_name}",
        f" Timezone : {tz_name}",
        f" Updated  : {updated_local}",
        f" Periods  : showing {shown} of {total}",
        " Legend: RH = Relative Humidity | PoP = Probability of Precipitation",
        " Note: Some fields may be N/A depending on endpoint data availability",
    ]

    width = max(len(header), len(divider), max(len(s) + 3 for s in info_lines))
    if width < 100:
        width = 100

    # Banner
    print(_hr_line(width))
    print(_center_line("NOAA / NWS HOURLY FORECAST CLI", width))
    print(_hr_line(width))

    print(_left_line(f" Location : {city_name}", width))
    print(_left_line(f" Timezone : {tz_name}", width))
    print(_left_line(f" Updated  : {updated_local}", width))
    print(_left_line(f" Periods  : showing {shown} of {total}", width))
    print(_hr_line(width))

    # Table header
    print(header)
    print(divider)

    # Table rows
    for i, p in enumerate(periods[:shown], start=1):
        # Time
        start_str = p.get("startTime")
        try:
            local_time = _to_local_str(start_str, tz_name) if start_str else "N/A"
        except Exception:
            local_time = str(start_str)

        # Temperature (supports numeric or QuantitativeValue)
        temp_val = p.get("temperature")
        temp_unit = p.get("temperatureUnit", "")
        temp_s = _fmt_qv(temp_val)
        if temp_s != "N/A" and temp_unit:
            temp_s = f"{temp_s}{temp_unit}"

        # Wind
        wind_speed = p.get("windSpeed", "N/A")
        wind_dir = p.get("windDirection", "")
        wind_s = f"{wind_speed} {wind_dir}".strip()

        # RH / PoP
        rh_s = _fmt_percent(p.get("relativeHumidity"))
        pop_s = _fmt_percent(p.get("probabilityOfPrecipitation"))

        # Forecast summary
        short_fcst = _truncate(p.get("shortForecast", "N/A"), col_fcst)

        row = (
            f"| {str(i):<{col_idx-1}}"
            f"| {_truncate(local_time, col_time):<{col_time}}"
            f"| {_truncate(temp_s, col_temp):<{col_temp}}"
            f"| {_truncate(wind_s, col_wind):<{col_wind}}"
            f"| {_truncate(rh_s, col_rh):<{col_rh}}"
            f"| {_truncate(pop_s, col_pop):<{col_pop}}"
            f"| {short_fcst:<{col_fcst}}|"
        )
        print(row)

    print(_hr_line(width))
    print(_left_line(" Legend: RH = Relative Humidity | PoP = Probability of Precipitation", width))
    print(_left_line(" Note: Some fields may be N/A depending on endpoint data availability", width))
    print(_hr_line(width))


# -------------------------
# USAGE
# -------------------------
print_forecast_cli(data, city_name="Eugene, OR", tz_name="America/Los_Angeles", limit=100)
