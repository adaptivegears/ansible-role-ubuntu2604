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

variable "b2_bucket" {
  description = "B2 bucket and stable prefix dedicated to the Forgejo Restic repository; do not include backup dates."
  type        = string
  nullable    = false

  validation {
    condition     = length(trimspace(var.b2_bucket)) > 0
    error_message = "Set the Forgejo repository bucket/prefix in terraform.tfvars.yaml."
  }
}

variable "backup_schedule" {
  description = "K8up cron expression for the online Forgejo PVC backup, including its timezone."
  type        = string
  default     = "CRON_TZ=UTC 0 3 * * *"
}

# ---------------------------------------------------------------------------
# Kustomization
# ---------------------------------------------------------------------------

resource "kustomization_resource" "schedule" {
  manifest = jsonencode({
    apiVersion = "k8up.io/v1"
    kind       = "Schedule"
    metadata = {
      name      = "forgejo-data"
      namespace = "forgejo"
    }
    spec = {
      # Isolate the repository while inheriting K8up's global endpoint and credentials.
      backend = { s3 = { bucket = var.b2_bucket } }
      backup = {
        schedule = var.backup_schedule
        labelSelectors = [{
          matchLabels = { "app.kubernetes.io/component" = "forgejo-data" }
        }]
        # The backup image defaults to UID 65532; root is needed to read all Forgejo files.
        # K8up mounts selected PVCs read-only; no application permissions are changed.
        podSecurityContext = {
          runAsUser  = 0
          runAsGroup = 0
        }
      }
      # No hooks, application shutdown, or automatic pruning of repository snapshots.
    }
  })
}
