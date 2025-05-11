# -------------------------------------------------------------------------- #
# Copyright 2002-2025, OpenNebula Project, OpenNebula Systems                #
#                                                                            #
# Licensed under the Apache License, Version 2.0 (the "License"); you may    #
# not use this file except in compliance with the License. You may obtain    #
# a copy of the License at                                                   #
#                                                                            #
# http://www.apache.org/licenses/LICENSE-2.0                                 #
#                                                                            #
# Unless required by applicable law or agreed to in writing, software        #
# distributed under the License is distributed on an "AS IS" BASIS,          #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   #
# See the License for the specific language governing permissions and        #
# limitations under the License.                                             #
#--------------------------------------------------------------------------- #

import threading
import logging
from collections import defaultdict
from flask import Flask, Response
from collector import periodic_gpu_vm_scan
from cache import metrics_cache
from helper import merge_prometheus_metrics_with_vm_id
from config import LOG_TO_FILE, LOG_TO_CONSOLE, LOG_FILE_PATH, EXPORTER_PORT

# Setup logging based on configuration
handlers = []
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

if LOG_TO_FILE:
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=5_000_000, backupCount=3)
    file_handler.setFormatter(log_formatter)
    handlers.append(file_handler)

if LOG_TO_CONSOLE:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    handlers.append(console_handler)

logging.basicConfig(level=logging.INFO, handlers=handlers)

app = Flask(__name__)

@app.route("/metrics")
def metrics():
    data = metrics_cache.dump_and_clear()
    output = merge_prometheus_metrics_with_vm_id(data)
    return Response(output, mimetype="text/plain")

if __name__ == "__main__":
    logging.info("Starting GPU VM metrics exporter service.")
    scan_thread = threading.Thread(target=periodic_gpu_vm_scan, daemon=True)
    scan_thread.start()
    app.run(host="0.0.0.0", port=EXPORTER_PORT)
