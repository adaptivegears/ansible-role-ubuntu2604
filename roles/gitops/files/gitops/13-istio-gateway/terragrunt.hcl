dependencies {
  paths = ["../10-gateway-api", "../11-istio-base", "../12-istiod"]
}

inputs = yamldecode(file("terraform.tfvars.yaml"))
