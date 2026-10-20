dependencies {
  paths = ["../10-gateway-api", "../11-istio-base", "../12-istiod"]
}

inputs = merge(
  yamldecode(file("terraform.tfvars.yaml")),
  yamldecode(sops_decrypt_file("terraform.tfvars.sops.yaml")),
)
