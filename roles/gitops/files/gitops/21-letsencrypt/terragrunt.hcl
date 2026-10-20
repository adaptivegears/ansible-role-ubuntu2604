dependencies {
  paths = ["../13-istio-gateway", "../20-cert-manager"]
}

inputs = yamldecode(file("terraform.tfvars.yaml"))
