import time
import logging
import concurrent.futures
import mysql.connector
from fabric import Connection
from invoke.exceptions import UnexpectedExit
from cache import metrics_cache
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, SCAN_INTERVAL, SSH_USER, SSH_KEY, REMOTE_SCRIPT

logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger("invoke").setLevel(logging.WARNING)
logging.getLogger("fabric").setLevel(logging.WARNING)

SQL_QUERY = """
SELECT oid,
       ExtractValue(body,'//HISTORY_RECORDS/HISTORY[last()]/HOSTNAME') AS hostname,
       ExtractValue(body,'count(//PCI[VENDOR="10de"])') as NVIDIA_DEVICES
FROM vm_pool
WHERE state=3 and ExtractValue(body,'count(//PCI[VENDOR="10de"])') > 0;
"""

def ensure_script_exists(conn):
    result = conn.run(f'test -f /tmp/{REMOTE_SCRIPT}', warn=True, hide=True)
    if result.ok:
        logging.debug(f"Script already exists on {conn.host}")
        return

    logging.info(f"Uploading script to {conn.host}")
    try:
        # Copiar archivo local a remoto
        conn.put(f'./scripts/{REMOTE_SCRIPT}', remote=f"/tmp/{REMOTE_SCRIPT}")

        # (Opcional) Dar permisos de ejecución
        conn.run(f"chmod +x /tmp/{REMOTE_SCRIPT}")
    except FileNotFoundError as e:
        print(f"Local file not found: {e}")
    except UnexpectedExit as e:
        print(f"Remote command failed: {e}")
    except Exception as e:
        print(f"General error during file transfer: {e}")

def run_remote_metrics_command(host, vm_id):
    try:
        with Connection(host=host, user=SSH_USER, connect_kwargs={"key_filename": SSH_KEY}) as conn:
            ensure_script_exists(conn)
            logging.info(f"Collecting metrics for VM {vm_id} on host {host}")
            result = conn.run(f"/tmp/{REMOTE_SCRIPT} {vm_id}", warn=True, hide=True)
            if result.ok:
                return result.stdout
            else:
                logging.warning(f"Remote command for VM {vm_id} on host {host} exited with code {result.return_code}")
                return None
    except Exception as e:
        #logging.error(f"Error fetching metrics from {host} for VM {vm_id}: {str(e)}")
        logging.error(f"Error fetching metrics from {host} for VM {vm_id}")
        return None

def periodic_gpu_vm_scan():
    while True:
        try:
            logging.info("Querying OpenNebula database for active GPU VMs...")
            DB_CONFIG = {
                'host': DB_HOST,
                'database': DB_NAME,
                'user': DB_USER,
                'password': DB_PASSWORD
            }
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(SQL_QUERY)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            logging.info(f"Found {len(rows)} VMs with GPUs assigned.")

            def process_vm(row):
                vm_id, hostname, _ = row
                metrics = run_remote_metrics_command(hostname, vm_id)
                if metrics:
                    metrics_cache.store(str(vm_id), metrics)
                    logging.info(f"Metrics stored for VM {vm_id}")
                else:
                    logging.warning(f"Skipping storage: No metrics retrieved for VM {vm_id}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(process_vm, rows)

        except Exception as db_ex:
            logging.error(f"Database error: {db_ex}")
        time.sleep(SCAN_INTERVAL)
