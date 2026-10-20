dependencies {
  paths = ["../10-gateway-api"]
}

inputs = merge(
  yamldecode(file("terraform.tfvars.yaml")),
  yamldecode(sops_decrypt_file("terraform.tfvars.sops.yaml")),
)
