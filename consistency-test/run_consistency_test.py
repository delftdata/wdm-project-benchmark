import asyncio
import os
import shutil
import subprocess
import logging
from tempfile import gettempdir

from verify import verify_systems_consistency
from populate import populate_databases

STRESS_TEST_EXECUTION_TIME = 30  # Seconds

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
                    datefmt='%I:%M:%S')
logger = logging.getLogger("Consistency test")


# Create the tmp folder to store the logs, the users and the stock
logger.info("Creating tmp folder...")
tmp_folder_path: str = os.path.join(gettempdir(), 'wdm_consistency_test')

if os.path.isdir(tmp_folder_path):
    shutil.rmtree(tmp_folder_path)

os.mkdir(tmp_folder_path)
logger.info("tmp folder created")

# Populate the payment and stock databases
logger.info("Populating the databases...")
asyncio.run(populate_databases(tmp_folder_path))
logger.info("Databases populated")

# Run the load test
logger.info("Starting the load test...")
subprocess.call(["locust", "-f", "locustfile.py", "--host=''", f"--logfile={tmp_folder_path}/consistency-test.log",
                 "--headless", "-u", "1000", "-r", "1000", f"--run-time={STRESS_TEST_EXECUTION_TIME}s"],
                stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
logger.info("Load test completed")

# Verify the systems' consistency
logger.info("Starting the consistency evaluation...")
asyncio.run(verify_systems_consistency(tmp_folder_path))
logger.info("Consistency evaluation completed")

if os.path.isdir(tmp_folder_path):
    shutil.rmtree(tmp_folder_path)
