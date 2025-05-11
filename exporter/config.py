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

