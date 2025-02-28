#!/usr/bin/env bash
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


source /shell_lib.sh

function __config__(){
    cat <<EOF
configVersion: v1
kubernetesValidating:
- name: network-best-practices.example.com

  labelSelector:
    matchLabels:
      # helm adds a 'name' label to a namespace it creates
      name: networking
  rules:
  - apiGroups:   ["networking.gke.io"]
    apiVersions: ["v1"]
    operations:  ["CREATE", "UPDATE"]
    resources:   ["networks"]
    scope:       "Cluster"
EOF
}

function __on_validating::network-best-practices.example.com() {
  echo $BINDING_CONTEXT_PATH
      cat <<EOF > $VALIDATING_RESPONSE_PATH
{"  ":false, "message":"DEBUG--$BINDING_CONTEXT_PATH"}
EOF
  interfaceName=$(context::jq -r '.review.request.object.spec.nodeInterfaceMatcher.interfaceName')
  echo "Got interfaceName: $interfaceName"
  
  for A in $(kubectl  get network   -o jsonpath='{range .items[*]}{.spec.nodeInterfaceMatcher.interfaceName}{"\n"}{end}'); 
  do
    if [[ ! -z $A ]];
    then 
      if [[ $interfaceName == $A ]] ; then
cat <<EOF > $VALIDATING_RESPONSE_PATH
{"allowed":true}
EOF
      else
        if [[ $interfaceName == bond0.2-peer* ]] ; then
cat <<EOF > $VALIDATING_RESPONSE_PATH
{"allowed":false, "message":"Best Practices detects that $interfaceName cannot be used as a NetworkInterface"}
EOF
        else
cat <<EOF > $VALIDATING_RESPONSE_PATH
{"allowed":false, "message":"Best Practices detects that $interfaceName is not created in this cluster "}
EOF
        fi
      fi
    fi
  done
}

hook::run $@
