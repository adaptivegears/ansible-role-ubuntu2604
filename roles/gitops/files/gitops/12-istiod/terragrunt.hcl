dependencies {
  paths = ["../10-gateway-api", "../11-istio-base"]
}

inputs = merge(
  yamldecode(file("terraform.tfvars.yaml")),
  yamldecode(sops_decrypt_file("terraform.tfvars.sops.yaml")),
)
