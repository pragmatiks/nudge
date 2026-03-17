import logging
import os

import uvicorn

from src.api.server import create_app

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
# Quiet noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting Nudge...")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8787"))
    reload = os.getenv("RELOAD", "").lower() in ("1", "true")
    if reload:
        uvicorn.run(
            "src.api.server:create_app",
            factory=True,
            host=host,
            port=port,
            reload=True,
            reload_dirs=["src", "config"],
        )
    else:
        app = create_app()
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
