import os

# Database
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "dbname")
DB_USER = os.getenv("DB_USER", "dbuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "dbpassword")

# Scan interval
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", 10))

# SSH
SSH_USER = os.getenv("SSH_USER", "user")
SSH_KEY = os.getenv("SSH_KEY", "./id_rsa")
REMOTE_SCRIPT = os.getenv("REMOTE_SCRIPT", "get_gpu_metrics_from_vm.sh")

# Logging
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() == "true"
LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "gpu_vm_exporter.log")

#CACHE
CACHE_TTL = os.getenv("CACHE_TTL", 30)

#EXPORTER
EXPORTER_PORT = os.getenv("EXPORTER_PORT", 9835)

