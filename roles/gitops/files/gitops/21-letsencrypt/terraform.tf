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

variable "acme_email" {
  description = "Let's Encrypt account contact email."
  type        = string
}

variable "acme_server" {
  description = "ACME directory URL; override with the staging directory when testing issuance."
  type        = string
  default     = "https://acme-v02.api.letsencrypt.org/directory"
}

# ---------------------------------------------------------------------------
# Kustomization
# ---------------------------------------------------------------------------

resource "kustomization_resource" "cluster_issuer" {
  manifest = jsonencode({
    apiVersion = "cert-manager.io/v1"
    kind       = "ClusterIssuer"
    metadata = {
      name = "letsencrypt"
    }
    spec = {
      acme = {
        server = var.acme_server
        email  = var.acme_email
        privateKeySecretRef = {
          name = "letsencrypt-account-key"
        }
        solvers = [{
          http01 = {
            gatewayHTTPRoute = {
              parentRefs = [{
                name        = "gateway"
                namespace   = "istio-system"
                kind        = "Gateway"
                sectionName = "http"
              }]
            }
          }
        }]
      }
    }
  })
}
