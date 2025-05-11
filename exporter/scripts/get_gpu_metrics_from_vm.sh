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

#!/bin/bash
VM_NAME="one-$1"
EXPORTER_URL="http://localhost:9835/metrics"

if [ -z "$VM_NAME" ]; then
  echo "Usage: $0 <vm_id>"
  exit 1
fi

# Execute curl command inside VM 
EXEC_RESULT=$(virsh -c qemu:///system qemu-agent-command "$VM_NAME" \
  "{\"execute\": \"guest-exec\", \"arguments\": {\"path\": \"/usr/bin/curl\", \"arg\": [\"$EXPORTER_URL\"], \"capture-output\": true}}" 2>/dev/null)

PID=$(echo "$EXEC_RESULT" | jq -r '.return.pid // empty')

if [ -z "$PID" ]; then
  echo "# Failed to initiate command in VM: $VM_NAME"
  exit 1
fi

# Wait command execution
sleep 2

# Obtain execution status and output
STATUS=$(virsh -c qemu:///system qemu-agent-command "$VM_NAME" \
  "{\"execute\": \"guest-exec-status\", \"arguments\": {\"pid\": $PID}}" 2>/dev/null)

# Extract exit code and output
EXITCODE=$(echo "$STATUS" | jq -r '.return.exitcode // empty')
OUT_DATA=$(echo "$STATUS" | jq -r '.return["out-data"] // empty')

# If not Exitcode then exit 1
if [ -z "$EXITCODE" ]; then
  echo "# No exitcode received from VM guest agent"
  exit 1
fi

# If ouput decode and return 
if [ -n "$OUT_DATA" ]; then
  echo "$OUT_DATA" | base64 -d
fi

exit "$EXITCODE"
