import os
import shutil
import subprocess
import logging

from verify import verify_systems_consistency
from populate import populate_databases

STRESS_TEST_EXECUTION_TIME = 30  # Seconds

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
                    datefmt='%I:%M:%S')
logger = logging.getLogger("Consistency test")


# Create the tmp folder to store the logs, the users and the stock
logger.info("Creating tmp folder...")
current_file_directory: str = os.path.dirname(os.path.realpath(__file__))
tmp_folder_path: str = os.path.join(current_file_directory, 'tmp')
tmp_folder_exists: bool = os.path.isdir(tmp_folder_path)

if tmp_folder_exists:
    shutil.rmtree(tmp_folder_path)
os.mkdir(tmp_folder_path)
logger.info("tmp folder created")

# Populate the payment and stock databases
logger.info("Populating the databases...")
populate_databases()
logger.info("Databases populated")

# Run the load test
logger.info("Starting the load test...")
subprocess.call(["locust", "-f", "locustfile.py", "--host=''", "--logfile=tmp/consistency-test.log", "--headless",
                 "-u", "1000", "-r", "1000", f"--run-time={STRESS_TEST_EXECUTION_TIME}s"],
                stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
logger.info("Load test completed")

# Verify the systems' consistency
logger.info("Starting the consistency evaluation...")
verify_systems_consistency()
logger.info("Consistency evaluation completed")
