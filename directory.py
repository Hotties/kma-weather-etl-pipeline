import os
import logging

def make_dir():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    logging.basicConfig( 
        filename = "logs/pipeline.log",
        level = logging.INFO,
        format = "%(asctime)s - %(levelname)s - %(message)s",
        encoding = "utf-8"
        )
