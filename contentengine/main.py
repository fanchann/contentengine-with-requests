import os

os.environ["PLAYWRIGHT_SETUP_SKIP"] = "1"

from master.app import app # noqa: E402
from master.integration import playwright  # noqa: E402

playwright.setup(app)

from contentengine.app.main import * # noqa
