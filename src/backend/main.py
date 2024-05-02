# flake8: noqa: E402 (module level import not at top of file)
import os
import sys
import asyncio
import psutil
import uvloop
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

# add total project layout to path
sys.path.append(".")

# set event loop policy
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # type: ignore

from src.config import settings
from src.backend.app import app  # noqa: F401 (imported but unused)


def main(
    workers: int = 1,
    reload: bool = False,
    max_requests: int = 500,
):
    """Method to launch the backend API server

    Parameters
    ----------
    workers : int
        The `workers` parameter is an optional integer that determines the number
        of workers to launch the backend API server with. If -1, then the
        number of workers will be equal to the number of physical cores.

        Workers rule of thumb:
            workers = 2 * physical_num_cores + 1

        However, physical cores can have multiple logical cores running at once due
        to hyperthreading. As a result, the number of workers should be equal to
        the number of logical cores.
        Default is 1.
    reload : bool
        The `reload` parameter is a boolean that determines if the backend API
        server should be launched with auto-reload enabled. This is only
        applicable when using Uvicorn or Granian.
    max_requests : int
        The `max_requests` parameter is an optional integer that determines the
        maximum number of requests a worker will process before restarting. Only
        applicable when using Gunicorn.

    Returns
    -------
    None
    """
    ## Workers
    physical_cores = psutil.cpu_count(logical=False)
    if physical_cores is None:
        physical_cores = 1
    if workers == -1:
        workers = physical_cores
    else:
        assert (
            workers <= (2 * physical_cores + 1)
        ), "Number of workers must be less than or equal to the number of 2 * num physical cores + 1"

    ## Launch string
    launch_str = (
        f"uvicorn src.backend.main:app "
        "--loop uvloop "
        "--http httptools "
        f"--host {settings.backend_host} "
        f"--port {settings.backend_port} "
        f"--limit-max-requests {max_requests} "
        f"--workers {workers if not reload else 1}"
    )

    # Add reload flag
    if reload:
        launch_str += " --reload"

    ## Launch
    os.system(launch_str)


if __name__ == "__main__":
    # Parse command line arguments
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=1,
        help="Number of workers to launch backend API server with.",
    )
    parser.add_argument(
        "-r",
        "--reload",
        action="store_true",
        help="Launch backend API server with auto-reload enabled. Only applicable when using Uvicorn or Granian.",
    )
    parser.add_argument(
        "-m",
        "--max_requests",
        type=int,
        default=500,
        help="Maximum number of requests a worker will process before restarting. Only applicable when using Gunicorn.",
    )
    kwargs = vars(parser.parse_args())
    main(**kwargs)
