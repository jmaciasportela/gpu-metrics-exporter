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

# # Expresión regular para capturar líneas de métricas
# METRIC_LINE_REGEX = re.compile(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)({.*?})?\s+(.*)$')

# def add_label_to_metric_line(line, label_key, label_value):
#     match = METRIC_LINE_REGEX.match(line)
#     if not match:
#         return line  # No es una línea de métrica, mantener igual

#     metric_name, labels_str, value = match.groups()
#     if labels_str:
#         # Ya tiene etiquetas, agregar la nueva
#         labels_str = labels_str[:-1] + f',{label_key}="{label_value}"' + '}'
#     else:
#         # No tiene etiquetas, crear un bloque
#         labels_str = f'{{{label_key}="{label_value}"}}'

#     return f'{metric_name}{labels_str} {value}\n'

def add_vm_id_to_metric_line(line, vm_id):
    """Agrega vm_id como label a una línea de métrica Prometheus."""
    if line.startswith('#') or line.strip() == '':
        return line  # no modificar comentarios ni líneas vacías

    # Métrica con labels
    match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)({.*})\s+(.*)$', line)
    if match:
        name, labels, value = match.groups()
        # Insertar vm_id como nuevo label
        labels = labels[:-1] + f',vm_id="{vm_id}"' + '}'
        return f"{name}{labels} {value}"

    # Métrica sin labels
    match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\s+(.*)$', line)
    if match:
        name, value = match.groups()
        labels = f'{{vm_id="{vm_id}"}}'
        return f"{name}{labels} {value}"

    # En caso de no coincidir, devuelve la línea sin cambios
    return line

def merge_prometheus_metrics_with_vm_id(vm_metric_dict):
    """
    Combina respuestas Prometheus de múltiples VMs agregando vm_id como label
    y agrupando correctamente HELP/TYPE y valores.
    
    :param vm_metric_dict: dict donde clave=vm_id, valor=respuesta /metrics en texto
    :return: string de métricas combinadas
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
                # Es una línea de datos: agregar vm_id y clasificar por métrica
                enriched_line = add_vm_id_to_metric_line(line, vm_id)
                metric_match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)', enriched_line)
                if metric_match:
                    metric_name = metric_match.group(1)
                    data_lines[metric_name].append(enriched_line)

    # Construir salida
    output = []
    for metric_name in sorted(data_lines.keys()):
        meta = help_type_blocks.get(metric_name, {})
        if meta.get("HELP"):
            output.append(meta["HELP"])
        if meta.get("TYPE"):
            output.append(meta["TYPE"])
        output.extend(data_lines[metric_name])
        output.append("")  # Separador

    return "\n".join(output)