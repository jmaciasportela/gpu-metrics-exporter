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

import re
from collections import defaultdict

def add_vm_id_to_metric_line(line, vm_id):
    """Agrega vm_id como label a una línea de métrica Prometheus."""
    if line.startswith('#') or line.strip() == '':
        return line  # Dont modify comments or empty lines
    
    # Regex to detect metric lines with labels
    match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)({.*})\s+(.*)$', line)
    if match:
        name, labels, value = match.groups()
        # Insert vm_id as additional label
        labels = labels[:-1] + f',vm_id="{vm_id}"' + '}'
        return f"{name}{labels} {value}"

    # Regex to detect metric lines without labels
    match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\s+(.*)$', line)
    if match:
        name, value = match.groups()
        labels = f'{{vm_id="{vm_id}"}}'
        return f"{name}{labels} {value}"

    # If not coincidence return as is 
    return line

def merge_prometheus_metrics_with_vm_id(vm_metric_dict):
    """
    Combines Prometheus responses from multiple VMs by adding vm_id as a label
    and properly grouping HELP/TYPE headers and metric values.

    :param vm_metric_dict: dict where the key is vm_id and the value is the /metrics response as text
    :return: combined metrics as a single string
    """
    help_type_blocks = {}  # metric_name -> {"HELP": ..., "TYPE": ...}
    data_lines = defaultdict(list)  # metric_name -> list of lines

    metric_header_re = re.compile(r'^# (HELP|TYPE) (\S+)')

    for vm_id, text in vm_metric_dict.items():
        for line in text.splitlines():
            if line.startswith('#'):
                match = metric_header_re.match(line)
                if match:
                    meta_type, metric_name = match.groups()
                    if metric_name not in help_type_blocks:
                        help_type_blocks[metric_name] = {}
                    if meta_type not in help_type_blocks[metric_name]:
                        help_type_blocks[metric_name][meta_type] = line
            elif line.strip():
                # metric line: add vm_id and clasify by metric type
                enriched_line = add_vm_id_to_metric_line(line, vm_id)
                metric_match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)', enriched_line)
                if metric_match:
                    metric_name = metric_match.group(1)
                    data_lines[metric_name].append(enriched_line)

    # Output
    output = []
    for metric_name in sorted(data_lines.keys()):
        meta = help_type_blocks.get(metric_name, {})
        if meta.get("HELP"):
            output.append(meta["HELP"])
        if meta.get("TYPE"):
            output.append(meta["TYPE"])
        output.extend(data_lines[metric_name])
        output.append("")
        
    return "\n".join(output)