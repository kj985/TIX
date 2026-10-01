"""Command line entry point:

    python -m gigtool run             start the dashboard
    python -m gigtool import          import gigs from Bandsintown
    python -m gigtool import --sample import the sample gigs
    python -m gigtool clear-sample    delete the sample gigs

(start.sh runs these for you, e.g. ./start.sh import)
"""
import argparse
import sys
import threading
import webbrowser

from . import BASE_DIR, DB_PATH, SAMPLE_EVENTS_PATH
from .config import ConfigError, load_config
from .db import connect
from .gigs import delete_source
from .importer import run_bandsintown_import, run_sample_import
from .sources.bandsintown import BandsintownError


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="gigtool", description="Sarah McLeod gig tool")
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="start the dashboard")
    run_p.add_argument("--no-browser", action="store_true", help="don't open a browser tab")
    imp = sub.add_parser("import", help="import upcoming gigs from Bandsintown")
    imp.add_argument("--sample", action="store_true", help="import the sample gigs instead")
    sub.add_parser("clear-sample", help="delete the sample gigs")
    args = parser.parse_args(argv)

    try:
        config = load_config(BASE_DIR)
    except ConfigError as e:
        print(f"Settings problem: {e}")
        return 1

    if args.command == "run":
        from .web import create_app

        url = f"http://localhost:{config.port}"
        print(f"\nGig dashboard running at {url}")
        print("Leave this window open while you use it. Press Ctrl+C to stop.\n")
        if not args.no_browser:
            threading.Timer(1.0, webbrowser.open, args=[url]).start()
        create_app(BASE_DIR, DB_PATH).run(host="127.0.0.1", port=config.port)
        return 0

    conn = connect(DB_PATH)
    if args.command == "import":
        try:
            if args.sample:
                result = run_sample_import(conn, config, SAMPLE_EVENTS_PATH)
            else:
                result = run_bandsintown_import(conn, config)
        except BandsintownError as e:
            print(f"Import failed: {e}")
            return 1
        print(f"Import finished: {result.summary()}.")
    elif args.command == "clear-sample":
        print(f"Deleted {delete_source(conn, 'sample')} sample gigs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
