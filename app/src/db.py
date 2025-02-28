import logging

import ibis
from ibis.backends.duckdb import Backend

DB_NAME = "flood_mapping"

log = logging.getLogger(__name__)


def connect() -> Backend:
    """Connect to Motherduck and load the spatial extension."""
    con = ibis.connect(f"duckdb://md:{DB_NAME}")

    con.load_extension("spatial")
    ibis.options.default_backend = con

    try:
        get_ipython()  # type: ignore
        log.info(
            "get_ipython() succeeded, probably an interactive session, setting ibis to interactive mode"
        )
        ibis.options.interactive = True
    except NameError:
        pass

    return con
