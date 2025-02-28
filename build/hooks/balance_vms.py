#!/usr/bin/env python3
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import sys,os,jq,json
from kubernetes import client, config
sys.path.append('/py_common')
import functions
from datetime import datetime
import time

def hook():
    config_map= {
        "configVersion": "v1",
        "kubernetes": [
            {
            "name": "balance-vms",
            "apiVersion": "vm.cluster.gke.io/v1",
            "kind": "VirtualMachine",
            "nameSelector": {"matchNames": ["vm1", "vm2", "vm3"]},
            "queue": "balance-vms-queue",
            "executeHookOnEvent": [],
            }
        ],
        "schedule": [
            {"crontab":"*/10 * * * *",
             "includeSnapshotsFrom":["balance-vms"],
             "queue": "balance-vms-queue",
             },
        ]
    }
    print(config_map)


def trigger():
    with open(os.environ["BINDING_CONTEXT_PATH"],'r') as f:
        BINDING_CONTEXT_PATH_JSON=json.load(f)
    
    kubernetes_type=jq.all('.[0].type', BINDING_CONTEXT_PATH_JSON)

    #print(BINDING_CONTEXT_PATH_JSON)

    if kubernetes_type[0]=="Synchronization":
        jq_query=".[0].objects[]"
    else:
        jq_query='.[0].snapshots.["balance-vms"][]'

 
    for _json in jq.all(jq_query, BINDING_CONTEXT_PATH_JSON):
        print(_json)
        if not _json:
            print("No VMs found")
            exit()

        if functions.check_vm_running(_json):
            vm_name,vm_pod_node_name,robin_master_node_name=functions.get_respective_node_names(BINDING_CONTEXT_PATH_JSON,_json)
            if vm_pod_node_name==robin_master_node_name:
                print("Balancing VM for : " + vm_name)
                functions.migration_vm_conditional(vm_name,alignement_required=False)
                print("Migrate Complete for : " + vm_name)
            else:
                print("Migration not required.")
                

if __name__ == "__main__":
    functions.run_hook(hook,trigger)