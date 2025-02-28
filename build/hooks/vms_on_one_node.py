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
            "name": "vms-snapshot",
            "apiVersion": "kubevirt.io/v1",
            "kind": "VirtualMachineInstance",
            "executeHookOnEvent": [],
            "queue": "vms-on-one-node-queue",
            }
        ],
        "schedule": [
            {"crontab":"*/5 * * * *",
             "includeSnapshotsFrom":["vms-snapshot"],
             "queue": "vms-on-one-node-queue",
             },
        ]
    }
    print(config_map)


def trigger():


    with open(os.environ["BINDING_CONTEXT_PATH"],'r') as f:
        BINDING_CONTEXT_PATH_JSON=json.load(f)
    
    
    #print(BINDING_CONTEXT_PATH_JSON)
    kubernetes_type=jq.all('.[0].type', BINDING_CONTEXT_PATH_JSON)

    if kubernetes_type[0]=="Synchronization":
        jq_query=".[0].objects[]"
    else:
        jq_query='.[0].snapshots.["vms-snapshot"][]'

    
    vm_node_list=jq.all(jq_query+'.object.status.nodeName', BINDING_CONTEXT_PATH_JSON)
    if (functions.all_same(vm_node_list)):
        print("All VMs on the same node. Need to rebalance")
        for _json in jq.all(jq_query, BINDING_CONTEXT_PATH_JSON):
            print(_json)
            if not _json:
                print("No VMs found")
                exit()

            if functions.check_vm_running(_json):
                vm_name,vm_pod_node_name,_=functions.get_respective_node_names(BINDING_CONTEXT_PATH_JSON,_json)
                print("Balancing VM for : " + vm_name)
                functions.migration_vm(vm_name)
                print("Migrate Complete for : " + vm_name)
    else:
        print("VM's are not all deployed on 1 node.")
        print(vm_node_list)



        
if __name__ == "__main__":
    functions.run_hook(hook,trigger)