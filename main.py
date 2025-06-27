import argparse
import atexit
import logging
import os
import threading
import webbrowser

from gui.main import app
from hardware.hardwaremanager import HardwareManager
from logmodule import setup_logging

# ===============================================================================
# Default Configuration
# ===============================================================================
GUI_PORT = 9982
DEBUG = False
ADD_HARDWARE = True
SILENCE_LOGGING = True

# ===============================================================================
# Command-Line Argument Parsing
# ===============================================================================
parser = argparse.ArgumentParser(description="Run the Diamond GUI application.")
parser.add_argument(
    "--dev",
    action="store_true",
    help="Run in development mode: no hardware, debug/reload on, different port.",
)
args = parser.parse_args()

# --- Modify configuration if --dev flag is present ---
if args.dev:
    print("--- DEVELOPMENT MODE ACTIVATED ---")
    GUI_PORT += 1  # Use a different port to avoid conflicts
    ADD_HARDWARE = False
    DEBUG = True
    app.title = "DEV MODE | Diamond GUI"  # Add a title to distinguish the dev server
    print(f"Running on port: {GUI_PORT}")
    print("Hardware loading: DISABLED")
    print("Debug/Reloader: ENABLED")
    print(f"Browser tab title set to: '{app.title}'")
    print("---------------------------------")


RELOAD = True and DEBUG

# ===============================================================================
# Setup
# ===============================================================================
setup_logging()
logger = logging.getLogger(__name__)

# Get the singleton instance of the hardware manager.
hm = HardwareManager()

# Register the shutdown function to be called automatically on exit.
if ADD_HARDWARE:
    atexit.register(hm.shutdown)


# ===============================================================================
# Hardware Initialization in Background
# ===============================================================================
def initialize_hardware_in_background():
    """
    Target function for the background thread. This function will block
    until all hardware is initialized, but it won't block the main app server.
    """
    logger.info("Starting hardware initialization in a background thread...")
    try:
        # This is the long-running call.
        hm.add_default_hardware()
        logger.info("Background hardware initialization is complete.")
    except Exception as e:
        logger.error(
            f"An error occurred during hardware initialization: {e}", exc_info=True
        )


# --- Reliable logic to decide if we should load hardware ---
should_load_hardware = False
if not RELOAD:
    # If the reloader is OFF, there is only one process. Always load.
    logger.info("Reloader is disabled. Will attempt to load hardware.")
    should_load_hardware = True
else:
    # If the reloader is ON, check for the environment variable set by Werkzeug.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        logger.info(
            "Werkzeug reloader: This is the main child process. Will attempt to load hardware."
        )
        should_load_hardware = True
    else:
        logger.info(
            "Werkzeug reloader: This is the initial watcher process. Skipping hardware load."
        )

if should_load_hardware and ADD_HARDWARE:
    # We are in the correct process, so start the background loading thread.
    hardware_thread = threading.Thread(
        target=initialize_hardware_in_background, daemon=True
    )
    hardware_thread.start()
elif not ADD_HARDWARE:
    # If hardware is disabled, mark as complete so the UI doesn't wait forever.
    hm.initialization_complete = True
    logger.info("ADD_HARDWARE is False. Skipping hardware initialization.")


# ===============================================================================
# Start the Dash GUI (this now runs immediately)
# ===============================================================================
logger.info(f"Starting Dash server on http://127.0.0.1:{GUI_PORT}")

if not DEBUG:
    # Use a timer to open the browser after the server has had a moment to start.
    threading.Timer(
        1.0, lambda: webbrowser.open(f"http://127.0.0.1:{GUI_PORT}")
    ).start()

app.run(
    host="0.0.0.0",
    port=GUI_PORT,
    threaded=True,  # IMPORTANT: single-threaded only with the built-in WSGI server!! Needed for complex app
    debug=DEBUG,
    use_reloader=RELOAD,
    dev_tools_silence_routes_logging=SILENCE_LOGGING,
)
