import logging
import shutil
import warnings

# Set up package-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with formatting
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Check for ipopt solver
if shutil.which("ipopt") is None:
    warnings.warn(
        "The 'ipopt' solver was not found on the system PATH. "
        "IDAES calculations require IPOPT. Please ensure it is installed and accessible.",
        RuntimeWarning
    )
else:
    logger.debug("IPOPT solver found on system PATH.")
