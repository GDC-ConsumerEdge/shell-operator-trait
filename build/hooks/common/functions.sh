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

function common::run_hook() {
  if [[ $1 == "--config" ]] ; then
    hook::config
  else
    hook::trigger
  fi
}

function kubectl::replace_or_create() {
  object=$(cat)

  if ! kubectl get -f - <<< "$object" >/dev/null 2>/dev/null; then
    kubectl create -f - <<< "$object" >/dev/null
  else
    kubectl replace --force -f - <<< "$object" >/dev/null
  fi
}
