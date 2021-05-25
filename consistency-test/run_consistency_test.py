import os
import shutil
import subprocess
import logging

from verify import verify_systems_consistency
from populate import populate_databases

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
                    datefmt='%I:%M:%S')
logger = logging.getLogger("Consistency test")

logger.info("Creating tmp folder...")
current_file_directory: str = os.path.dirname(os.path.realpath(__file__))
tmp_folder_path: str = os.path.join(current_file_directory, 'tmp')
tmp_folder_exists: bool = os.path.isdir(tmp_folder_path)

if tmp_folder_exists:
    shutil.rmtree(tmp_folder_path)
os.mkdir(tmp_folder_path)
logger.info("tmp folder created")
logger.info("Populating the databases...")
populate_databases()
logger.info("Databases populated")
logger.info("Starting the load test...")
subprocess.call(["locust", "-f", "locustfile.py", "--host=''", "--logfile=tmp/consistency-test.log", "--headless",
                 "-u", "1000", "-r", "1000", "--run-time=15s"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
logger.info("Load test completed")
logger.info("Starting the consistency evaluation...")
verify_systems_consistency()
logger.info("Consistency evaluation completed")
