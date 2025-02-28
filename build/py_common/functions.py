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

import random
import sys
import time
from datetime import datetime,timedelta
import  jq
from kubernetes import client, config


def run_hook(hook,trigger):
    if len(sys.argv)>1 and sys.argv[1] == "--config":
        return hook()
    else:
        return trigger()
    s

def kube_api():
    config.load_config()
    v1 = client.CoreV1Api()
    v1_custom=client.CustomObjectsApi()
    return v1,v1_custom

def exponential_backoff(func, max_retries=5, base_delay=120, max_delay=500,retry_fail="Hook Automation is unable to balance VM and node, existing"):
  """
  Decorator that implements exponential backoff for a function.

  Args:
    func: The function to decorate.
    max_retries: The maximum number of retries.
    base_delay: The initial delay in seconds.
    max_delay: The maximum delay in seconds.

  Returns:
    The decorated function.
  """
  def wrapper(*args, **kwargs):
    retries = 0
    delay = base_delay
    while retries <= max_retries:
      try:
        return func(*args, **kwargs)
      except Exception as e:
        print(f"Error: {e}")
        if retries == max_retries:
          print(retry_fail)
          raise Exception("unable to balance VM and Robin Master. Exiting")
        retries += 1
        delay = min(delay * 2, max_delay)
        jitter = random.uniform(0, 1)  # Add jitter to avoid synchronized retries
        sleep_time = delay + jitter
        print(f"Retrying in {sleep_time:.2f} seconds...")
        time.sleep(sleep_time)
  return wrapper


def migration_vm(vm_name):
    _,v1_custom=kube_api()
    start = datetime.now()
    date_time = start.strftime("%m-%d-%Y-%H%M")
    
    migration_resource= {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachineInstanceMigration",
        "metadata": { "name": "mig-job-hook-"+str(date_time), "namespace": "vm-workloads"},
        "spec": {"vmiName": str(vm_name)},
    }
    try:
        v1_custom.create_namespaced_custom_object(group="kubevirt.io",version="v1", plural="virtualmachineinstancemigrations", namespace="vm-workloads", body=migration_resource)
        while True:
            current_time = datetime.now()
            time_difference = current_time - start
            v1_custom.get_namespaced_custom_object_status(group="kubevirt.io",version="v1", plural="virtualmachineinstancemigrations", namespace="vm-workloads", name="mig-job-hook-"+str(date_time))
            if time_difference > timedelta(minutes=10) and  v1_custom["status"]["phase"] != "Succeeded":
                raise("Migration "+ "mig-job-hook-"+str(date_time) +" has taken over 10 minutes")
            elif v1_custom["status"]["phase"] == "Succeeded":
                break
    except Exception as e:
        print(f"Error: {e}")
    
    #time.sleep(120)

@exponential_backoff
def migration_vm_conditional(vm_name,alignement_required=False):

    migration_vm(vm_name)

    time.sleep(120)
    vm_name,vm_pod_node_name,robin_master_node_name=get_respective_node_names()

    if alignement_required and (vm_pod_node_name==robin_master_node_name):
        print("VM and Robin are on same nodes. Migration Complete.")
    elif not alignement_required and (vm_pod_node_name!=robin_master_node_name):
        print("VM and Robin Master are on different node. Migration Complete.")
    else:
        raise Exception("Condtional Migration failed for VM. Retrying LiveMigration")

def get_respective_node_names(BINDING_CONTEXT_PATH_JSON,parsed_json=None):
    v1,v1_custom=kube_api()
    robin_master_node_name = v1.list_namespaced_pod(namespace='robinio', label_selector='app=robin-master').items[0].spec.node_name
    kubernetes_type=jq.all('.[0].type', BINDING_CONTEXT_PATH_JSON)

    if parsed_json:
        vm_name= str(jq.all('.object.metadata.name',parsed_json)[0])
    elif kubernetes_type[0]=="Synchronization":
        vm_name= str(jq.all('.[0].objects[].object.metadata.name',BINDING_CONTEXT_PATH_JSON)[0])
    else:
        vm_name=str(jq.all('.[0].object.metadata.name', BINDING_CONTEXT_PATH_JSON)[0])
    
    vm_pod_name=v1_custom.get_namespaced_custom_object(group="vm.cluster.gke.io", version="v1", plural="virtualmachines",name=vm_name,namespace="vm-workloads")["status"]["interfaces"][0]["podName"]
    vm_pod_node_name=v1.read_namespaced_pod(name=vm_pod_name,namespace="vm-workloads").spec.node_name
    
    print("VM is:" + str(vm_name))
    print("Current VM's node name is: " + str(vm_pod_node_name))
    print("Current Robin Primary node is: " + str(robin_master_node_name))

    return str(vm_name),str(vm_pod_node_name), str(robin_master_node_name)
    
def check_vm_running(_json):
    if len(jq.all('.object.status',_json)[0])==0:
        print(_json["object"]["metadata"]["name"] + " has no status")
        return False

    if jq.all('.object.status.state',_json)[0] is not None and jq.all('.object.status.state',_json)[0] != "Running":
        print(_json["object"]["metadata"]["name"] + " is not running")
        return False

    if jq.all('.object.status.phase',_json)[0] is not None and jq.all('.object.status.phase',_json)[0] != "Running":
        print(_json["object"]["metadata"]["name"] + " is not running")
        return False

    print(_json["object"]["metadata"]["name"] + " is running")
    return True

def all_same(arr):
    if not arr:  # Handle empty arrays
        return True
    return all(x == arr[0] for x in arr)
