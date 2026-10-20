dependencies {
  paths = ["../10-gateway-api", "../11-istio-base"]
}

include "root" {
  path = find_in_parent_folders("root.hcl")
}

inputs = merge(
  yamldecode(file("terraform.tfvars.yaml")),
  yamldecode(sops_decrypt_file("terraform.tfvars.sops.yaml")),
)
