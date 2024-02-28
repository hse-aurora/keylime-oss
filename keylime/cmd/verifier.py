from keylime import config, keylime_logging
from keylime.web import VerifierServer
from keylime.common.migrations import apply
from keylime.mba import mba
import asyncio
import tornado.process

# from keylime.web import VerifierServer
from keylime.models.base import db_manager

logger = keylime_logging.init_logging("verifier")


def main() -> None:
    # if we are configured to auto-migrate the DB, check if there are any migrations to perform
    if config.has_option("verifier", "auto_migrate_db") and config.getboolean("verifier", "auto_migrate_db"):
        apply("cloud_verifier")

    # Explicitly load and initialize measured boot components
    mba.load_imports()

    # TODO: Remove
    # cloud_verifier_tornado.main()

    server = VerifierServer()
    tornado.process.fork_processes(0)
    asyncio.run(server.start())

    # db_manager.make_engine("cloud_verifier")

    # server = VerifierServer()
    # tornado.process.fork_processes(0)
    # asyncio.run(server.start())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
