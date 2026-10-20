dependencies {
  paths = ["../13-istio-gateway", "../21-letsencrypt", "../30-openebs", "../31-cnpg"]
}

inputs = merge(
  yamldecode(file("terraform.tfvars.yaml")),
  yamldecode(sops_decrypt_file("terraform.tfvars.sops.yaml")),
)
