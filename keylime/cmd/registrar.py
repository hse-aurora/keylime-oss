from keylime import config, keylime_logging, registrar_common
from keylime.common.migrations import apply
from keylime.models import da_manager, db_manager
from keylime.web import RegistrarServer

logger = keylime_logging.init_logging("registrar")


def main() -> None:
    logger.info("Starting Keylime registrar...")

    config.check_version("registrar", logger=logger)

    # if we are configured to auto-migrate the DB, check if there are any migrations to perform
    if config.has_option("registrar", "auto_migrate_db") and config.getboolean("registrar", "auto_migrate_db"):
        apply("registrar")

    registrar_common.start(
        config.get("registrar", "ip"),
        config.getint("registrar", "tls_port"),
        config.getint("registrar", "port"),
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)