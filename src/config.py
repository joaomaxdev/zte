# src/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration for SSH connection
hostname = os.getenv("SSH_HOSTNAME")
port = int(os.getenv("SSH_PORT"))
username = os.getenv("SSH_USERNAME")
password = os.getenv("SSH_PASSWORD")