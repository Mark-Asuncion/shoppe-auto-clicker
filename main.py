import argparse
from typing import List
from autoclicker import run_ev_loop, set_ctrl_c_handler
import sys
import os

VERSION="1.0.0"
APP_NAME="AutoClicker"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description='',
        exit_on_error=True
    )
    parser.add_argument(
        "-v", "--version",
        help="Shows the application version",
        action="store_true")

    parser.add_argument(
        "-l", "--log",
        help="Logs folder path default <app_path>\\logs\\",
        required=False,
        default="logs",
        nargs='?')

    parser.add_argument(
        "-s","--sleep",
        help="Delay amount in seconds default 10 second",
        required=False,
        default=10,
        nargs='?')

    args = parser.parse_args(sys.argv[1:])

    if args.version:
        print(f"{APP_NAME} version {VERSION}")
        sys.exit(0)

    logs_folder = os.path.join(
        os.path.dirname(__file__),
        args.log
    )
    try:
        int(args.sleep)
    except:
        print("Invalid --sleep argument. Argument must be a number")
        sys.exit(1)

    opts = {
        "logs_dir": logs_folder,
        "sleep": int(args.sleep)
    }

    set_ctrl_c_handler()
    run_ev_loop(opts)