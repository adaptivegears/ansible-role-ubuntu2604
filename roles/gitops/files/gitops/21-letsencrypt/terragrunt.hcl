dependencies {
  paths = ["../13-istio-gateway", "../20-cert-manager"]
}

inputs = merge(
  yamldecode(file("terraform.tfvars.yaml")),
  yamldecode(sops_decrypt_file("terraform.tfvars.sops.yaml")),
)
