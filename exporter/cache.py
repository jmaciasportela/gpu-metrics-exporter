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
import time
from config import CACHE_TTL

class MetricsCache:
    def __init__(self, ttl_seconds=CACHE_TTL):
        self.lock = threading.Lock()
        self.ttl = ttl_seconds
        self.data = {}
        self.output = {}

    def store(self, vm_id, metrics):
        now = time.time()
        with self.lock:
            self.data[vm_id] = None
            self.data[vm_id] = (now, metrics)

    def dump_and_clear(self):
        now = time.time()
        self.output.clear()
        self.output = self.data.copy()
        result = {}
        with self.lock:
            for vm_id, (ts, metrics) in list(self.output.items()):
                if now - ts <= self.ttl:
                    result[vm_id] = metrics
                else:
                    del self.data[vm_id]  # Clean cache if expired            
        return result

metrics_cache = MetricsCache()