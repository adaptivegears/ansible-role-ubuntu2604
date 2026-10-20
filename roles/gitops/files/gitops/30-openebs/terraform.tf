# ---------------------------------------------------------------------------
# Terraform
# ---------------------------------------------------------------------------

terraform {
  required_version = "~> 1.12.0"

  required_providers {
    kustomization = {
      source  = "kbst/kustomization"
      version = "~> 0.9"
    }
  }
}

provider "kustomization" {
  kubeconfig_path = "~/.kube/config"
}

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

variable "openebs_version" {
  description = "OpenEBS chart version."
  type        = string
  default     = "4.6.2"
}

# ---------------------------------------------------------------------------
# Kustomization
# ---------------------------------------------------------------------------

resource "kustomization_resource" "namespace" {
  manifest = jsonencode({
    apiVersion = "v1"
    kind       = "Namespace"
    metadata = {
      name = "openebs"
    }
  })
}

data "kustomization_overlay" "this" {
  namespace = "openebs"

  helm_charts {
    name         = "openebs"
    repo         = "https://openebs.github.io/openebs"
    release_name = "openebs"
    namespace    = "openebs"
    version      = var.openebs_version
    skip_tests   = true

    values_inline = yamlencode({
      engines = {
        local = {
          hostpath = {
            enabled = true
          }
          lvm = {
            enabled = false
          }
          zfs = {
            enabled = false
          }
          rawfile = {
            enabled = false
          }
        }
        replicated = {
          mayastor = {
            enabled = false
          }
        }
      }
      localpv-provisioner = {
        hostpathClass = {
          isDefaultClass = true
        }
      }
      loki = {
        enabled = false
        minio = {
          enabled = false
        }
      }
      alloy = {
        enabled = false
      }
    })
  }

  kustomize_options {
    enable_helm = true
    helm_path   = "/usr/local/bin/helm"
  }
}

resource "kustomization_resource" "p0" {
  for_each = data.kustomization_overlay.this.ids_prio[0]
  manifest = data.kustomization_overlay.this.manifests[each.value]

  depends_on = [kustomization_resource.namespace]
}

resource "kustomization_resource" "p1" {
  for_each = data.kustomization_overlay.this.ids_prio[1]
  manifest = data.kustomization_overlay.this.manifests[each.value]

  depends_on = [kustomization_resource.p0]
}

resource "kustomization_resource" "p2" {
  for_each = data.kustomization_overlay.this.ids_prio[2]
  manifest = data.kustomization_overlay.this.manifests[each.value]

  depends_on = [kustomization_resource.p1]
}

# ---------------------------------------------------------------------------
# StorageClass - Retain
# ---------------------------------------------------------------------------

resource "kustomization_resource" "openebs_hostpath_retain" {
  manifest = jsonencode({
    apiVersion = "storage.k8s.io/v1"
    kind       = "StorageClass"
    metadata = {
      name = "openebs-hostpath-retain"
      annotations = {
        "cas.openebs.io/config" = yamlencode([
          {
            name  = "StorageType"
            value = "hostpath"
          },
          {
            name  = "BasePath"
            value = "/var/openebs/local"
          },
        ])
        "openebs.io/cas-type" = "local"
      }
    }
    provisioner       = "openebs.io/local"
    reclaimPolicy     = "Retain"
    volumeBindingMode = "WaitForFirstConsumer"
  })

  depends_on = [kustomization_resource.p2]
}
