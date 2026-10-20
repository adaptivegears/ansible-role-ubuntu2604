dependencies {
  paths = ["../13-istio-gateway", "../21-letsencrypt", "../30-openebs", "../31-cnpg"]
}

include "root" {
  path = find_in_parent_folders("root.hcl")
}

inputs = merge(
  yamldecode(file("terraform.tfvars.yaml")),
  yamldecode(sops_decrypt_file("terraform.tfvars.sops.yaml")),
)
