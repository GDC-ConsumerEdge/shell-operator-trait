# Shell Operator


## Table of Contents
- [Shell Operator](#shell-operator)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [How to use](#how-to-use)
    - [Build the docker image](#build-the-docker-image)
    - [Create an overlay](#create-an-overlay)
    - [ACM Overview](#acm-overview)
  - [Disclaimer](#disclaimer)

## Overview

This repository follows ACM trait pattern with examples to be deployed onto Google Distributed Cloud Conencted Clusters.
Namely there are 3 examples that show how shell operator can be used to automate based on kubernete events occuring in the cluster. 

- Pod Affinity for VMs: 
  - In a specific given scenario where podAffinity is not being met, ensure VM(s) are migrated to the desired affinity that is required. In this example the vm called aligned-vm through shell-operator will be further  rensured to be deployed onto the same node as robin-master. Review [example](https://github.com/GDC-ConsumerEdge/shell-operator-trait/blob/main/build/hooks/migration_aligned_vm.py), [example2](https://github.com/GDC-ConsumerEdge/shell-operator-trait/blob/main/build/hooks/balance_vms.py) for more details.
```
  scheduling:
    affinity:
      podAffinity:
        preferredDuringSchedulingIgnoredDuringExecution:
          - podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: robin-master
              namespaces:
                - vm-workloads
                - robinio
              topologyKey: kubernetes.io/hostname
            weight: 100

```
- Load balancing VMs: In a specific given scenario where all VMs land on 1 node, ensure VM(s) are migrated over to other nodes for proper load balancing. In this example if 3 VM's [vm1,vm2,vm3] land onto 1 node, then VM Migration will take place. Review [example](https://github.com/GDC-ConsumerEdge/shell-operator-trait/blob/main/build/hooks/vms_on_one_node.py) for more details.
- Webhooks: Simiarly to OPA/Gatekeeper, here is an example network guardrail to stop users from deploy a bad network resource on to the cluster.Review [example](https://github.com/GDC-ConsumerEdge/shell-operator-trait/blob/main/build/hooks/validating.sh) for more details.

## How to use

### Build the docker image

`cd build`

`docker build -t gcr.io/PROJECT_NAME/shell-operator:TAG_NAME .`

`docker push gcr.io/PROJECT_NAME/shell-operator:TAG_NAME`

### Create an overlay

Create the `kustomization.yaml` file, replacing the patch value with the docker image path built in the previous step.

```
tree

.
├── overlays
│   └── shell-operator
│       └── kustomization.yaml
```

```
cat overlays/shell-operator/kustomization.yaml

apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- https://gitlab.com/gcp-solutions-public/retail-edge/available-cluster-traits/shell-operator-trait.git/config

patches:
- patch: |-
    - op: replace
      path: /spec/template/spec/containers/0/image
      value: gcr.io/PROJECT_NAME/shell-operator:TAG_NAME
  target:
    group: apps
    kind: Deployment
    name: shell-operator
    version: v1
```

Apply the following `RootSync`, changing the dir to match where you saved the overlay. 

```yaml
apiVersion: configsync.gke.io/v1beta1
kind: RootSync
metadata:
  name: shell-operator-trait-sync
  namespace: config-management-system
spec:
  sourceFormat: unstructured
  git:
    auth: "token"
    branch: "main"
    dir: "/config/clusters/CLUSTER_NAME/overlays/shell-operator"
    repo: "https://path/to/your/repo.git"
    secretRef:
      name: git-creds
  override:
    enableShellInRendering: true
```
After this is applied, this should deploy shell-operator with the said examples.

### ACM Overview

See [our documentation](https://cloud.google.com/anthos-config-management/docs/repo) for how to use each subdirectory.

## Disclaimer

This project is not an official Google project. It is not supported by
Google and Google specifically disclaims all warranties as to its quality,
merchantability, or fitness for a particular purpose.