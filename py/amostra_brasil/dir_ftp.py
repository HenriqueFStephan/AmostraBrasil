"""
List files on IBGE FTP for a given municipality code.
REMOTE DATA NOTE: FTP URL and layout may have changed since 2010 census.
"""

from typing import List
import urllib.request
import ssl

# Default base URL for 2010 census address files (by state) - may be outdated
DEFAULT_FTP_BASE = (
    "ftp://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/"
    "Cadastro_Nacional_de_Enderecos_Fins_Estatisticos"
)


def dir_ftp(my_url: str = "", codibge: str = "") -> List[str]:
    """
    List files in FTP directory whose filename starts with the 7-digit codibge.

    Parameters
    ----------
    my_url : str
        Full URL to the state folder, e.g.
        ftp://ftp.ibge.gov.br/.../Cadastro_Nacional_de_Enderecos_Fins_Estatisticos/AL/
    codibge : str
        7-character IBGE municipality code. Only filenames starting with this
        prefix are returned.

    Returns
    -------
    list of str
        Filenames (e.g. ZIP names) for that municipality.

    Remote data note
    ----------------
    IBGE may have moved or restructured FTP. If connection fails, check
    https://www.ibge.gov.br/ for current census data locations.
    """
    codibge = (codibge or "").strip()
    if len(codibge) < 7:
        codibge = codibge.zfill(7)
    prefix = codibge[:7]

    # Use urllib for FTP listing (no third-party deps). Some servers may require TLS.
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(my_url, timeout=60, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise RuntimeError(
            f"Failed to list FTP directory {my_url}. "
            "IBGE FTP structure may have changed (see REMOTE_DATA.md)."
        ) from e

    lines = [line.strip() for line in raw.replace("\r\n", "\n").split("\n") if line.strip()]
    result = []
    for line in lines:
        # NLST-style: one filename per line
        if line.startswith(prefix):
            result.append(line)
            continue
        # LIST-style: filename often last token
        parts = line.split()
        if parts and parts[-1].startswith(prefix):
            result.append(parts[-1])
    return result
