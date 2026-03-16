"""
Geocode addresses via Google Maps Geocoding API.
REMOTE DATA NOTE: Google now requires an API key. Set GOOGLE_GEOCODING_API_KEY in env.
"""

import os
import urllib.parse
from typing import Any, Dict, List, Optional

# Optional: use requests if available for clearer code
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


def _geocode_http(address: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Call Google Geocoding API. Returns dict with Lat, Lng, Ender, Status."""
    api_key = api_key or os.environ.get("GOOGLE_GEOCODING_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "Google Geocoding API key required. Set GOOGLE_GEOCODING_API_KEY or pass api_key."
        )
    encoded = urllib.parse.quote(address)
    url = (
        "https://maps.googleapis.com/maps/api/geocode/json"
        f"?address={encoded}&language=pt-BR&key={api_key}"
    )
    if _HAS_REQUESTS:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    else:
        import urllib.request
        with urllib.request.urlopen(url, timeout=10) as resp:
            import json
            data = json.loads(resp.read().decode())
    status = data.get("status", "UNKNOWN")
    if status != "OK":
        return {
            "Lat": None,
            "Lng": None,
            "Ender": "",
            "Status": status,
        }
    res = data.get("results", [{}])[0]
    geom = res.get("geometry", {}).get("location", {})
    return {
        "Lat": geom.get("lat"),
        "Lng": geom.get("lng"),
        "Ender": res.get("formatted_address", ""),
        "Status": status,
    }


def get_geo_code_cs(gc_str: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Geocode a single address using Google Maps Geocoding API.

    Parameters
    ----------
    gc_str : str
        Address string to geocode.
    api_key : str, optional
        Google API key. If not set, uses env var GOOGLE_GEOCODING_API_KEY.

    Returns
    -------
    dict
        Keys: Lat, Lng, Ender (formatted address), Status (e.g. OK, ZERO_RESULTS).
    """
    return _geocode_http(gc_str, api_key=api_key)


def set_lat_long(
    datafr: "pd.DataFrame",
    addresscol: List[str],
    api_key: Optional[str] = None,
) -> "pd.DataFrame":
    """
    Add columns Lat, Lng, End, Status to dataframe by geocoding each address.

    Parameters
    ----------
    datafr : pandas.DataFrame
        Table to augment.
    addresscol : list of str
        One address per row (same length as datafr).
    api_key : str, optional
        Google Geocoding API key.

    Returns
    -------
    pandas.DataFrame
        datafr with new columns Lat, Lng, End, Status.
    """
    import pandas as pd
    n = len(addresscol)
    rows = []
    for i in range(n):
        row = _geocode_http(addresscol[i], api_key=api_key)
        rows.append({
            "Lat": row["Lat"],
            "Lng": row["Lng"],
            "End": row["Ender"],
            "Status": row["Status"],
        })
    df_geo = pd.DataFrame(rows)
    return pd.concat([datafr.reset_index(drop=True), df_geo], axis=1)
