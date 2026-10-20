dependencies {
  paths = ["../13-istio-gateway", "../21-letsencrypt", "../30-openebs", "../31-cnpg"]
}

inputs = yamldecode(file("terraform.tfvars.yaml"))
