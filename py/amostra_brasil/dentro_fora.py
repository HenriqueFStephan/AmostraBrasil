"""
Mark points as inside or outside a polygon (e.g. municipality boundary).
"""

from typing import Optional

# Type hint for GeoDataFrame without requiring geopandas at import
try:
    import geopandas as gpd
    from shapely.geometry import Point
except ImportError:
    gpd = None  # type: ignore


def set_dentro_fora(
    pontos: "gpd.GeoDataFrame",
    limites: "gpd.GeoDataFrame",
    plot: bool = False,
) -> "gpd.GeoDataFrame":
    """
    Add column DENTRO (True if point is inside polygon, False otherwise).

    Parameters
    ----------
    pontos : geopandas.GeoDataFrame
        Point geometry column; must have same CRS as limites.
    limites : geopandas.GeoDataFrame
        Polygon(s) for the boundary (e.g. municipality).
    plot : bool
        If True, plot limites and points (blue=inside, red=outside).
        Requires matplotlib.

    Returns
    -------
    geopandas.GeoDataFrame
        pontos with new column DENTRO (boolean).
    """
    if gpd is None:
        raise ImportError("geopandas is required for set_dentro_fora")
    if limites.crs != pontos.crs:
        pontos = pontos.to_crs(limites.crs)
    # Union polygons if multiple
    if len(limites) > 1:
        boundary = limites.unary_union
    else:
        boundary = limites.geometry.iloc[0]
    dentro = pontos.geometry.within(boundary)
    out = pontos.copy()
    out["DENTRO"] = dentro

    if plot:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        limites.plot(ax=ax, facecolor="none", edgecolor="black")
        out[out["DENTRO"]].plot(ax=ax, color="blue", markersize=20)
        out[~out["DENTRO"]].plot(ax=ax, color="red", markersize=20)
        plt.show()
    return out
