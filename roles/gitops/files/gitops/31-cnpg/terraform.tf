# ---------------------------------------------------------------------------
# Terraform
# ---------------------------------------------------------------------------

terraform {
  required_version = "~> 1.12.0"

  backend "local" {
    path = "terraform.tfstate"
  }

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

variable "cnpg_version" {
  description = "CloudNativePG chart version, not the operator version."
  type        = string
  default     = "0.29.1"
}

# ---------------------------------------------------------------------------
# Kustomization
# ---------------------------------------------------------------------------

resource "kustomization_resource" "namespace" {
  manifest = jsonencode({
    apiVersion = "v1"
    kind       = "Namespace"
    metadata = {
      name = "cnpg-system"
    }
  })
}

data "kustomization_overlay" "this" {
  helm_charts {
    name         = "cloudnative-pg"
    repo         = "https://cloudnative-pg.github.io/charts"
    release_name = "cnpg"
    namespace    = "cnpg-system"
    version      = var.cnpg_version
    skip_tests   = true

    values_inline = yamlencode({
      crds = {
        create = true
      }
      config = {
        clusterWide = true
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
