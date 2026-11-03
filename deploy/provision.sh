#!/usr/bin/env bash
# Crea en Azure todo lo que necesita koza-ttp: grupo de recursos, VM Ubuntu 22.04 con
# IP pública fija, puertos 22/80/443 abiertos y un Azure AI Translator gratuito (F0).
# Se puede volver a correr: lo que ya existe se deja como está.
#
#   az login
#   bash deploy/provision.sh
set -euo pipefail

SUBSCRIPTION="${AZURE_SUBSCRIPTION_ID:-8907b1f1-8f8b-45ec-bb26-65438e9e267c}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-koza-ttp}"
LOCATION="${LOCATION:-southcentralus}"   # Texas: la región más cercana a México
VM_NAME="${VM_NAME:-vm-koza-ttp}"
VM_SIZE="${VM_SIZE:-Standard_B1s}"        # 1 vCPU / 1 GB (+ swap); subir a Standard_B2s si hace falta
ADMIN_USER="${ADMIN_USER:-ubuntu}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/koza_ttp_azure}"
TRANSLATOR_NAME="${TRANSLATOR_NAME:-translator-koza-ttp}"

az account set --subscription "${SUBSCRIPTION}"
for provider in Microsoft.Compute Microsoft.Network Microsoft.CognitiveServices; do
  az provider register --namespace "${provider}" --wait >/dev/null
done

if [ ! -f "${SSH_KEY}" ]; then
  ssh-keygen -t ed25519 -f "${SSH_KEY}" -N "" -C "koza-ttp-azure"
fi

az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" --output none

if ! az vm show --resource-group "${RESOURCE_GROUP}" --name "${VM_NAME}" >/dev/null 2>&1; then
  az vm create \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${VM_NAME}" \
    --image Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest \
    --size "${VM_SIZE}" \
    --admin-username "${ADMIN_USER}" \
    --ssh-key-values "${SSH_KEY}.pub" \
    --public-ip-sku Standard \
    --public-ip-address-allocation static \
    --os-disk-size-gb 30 \
    --output none
fi

for rule in "http 80 1010" "https 443 1020"; do
  set -- ${rule}
  az vm open-port --resource-group "${RESOURCE_GROUP}" --name "${VM_NAME}" \
    --port "$2" --priority "$3" --output none
done

if ! az cognitiveservices account show --resource-group "${RESOURCE_GROUP}" --name "${TRANSLATOR_NAME}" >/dev/null 2>&1; then
  az cognitiveservices account create \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${TRANSLATOR_NAME}" \
    --kind TextTranslation \
    --sku F0 \
    --location "${LOCATION}" \
    --yes \
    --output none
fi

IP="$(az vm show -d --resource-group "${RESOURCE_GROUP}" --name "${VM_NAME}" --query publicIps -o tsv)"
echo
echo "VM lista en ${IP}"
echo "  ssh -i ${SSH_KEY} ${ADMIN_USER}@${IP}"
echo
echo "DNS: apunta el registro A de koza-ttp.lesliedickinson.dev (y www.koza-ttp) a ${IP}"
echo
echo "Para el .env local (traducciones):"
echo "  AZURE_TRANSLATOR_KEY=<az cognitiveservices account keys list -g ${RESOURCE_GROUP} -n ${TRANSLATOR_NAME} --query key1 -o tsv>"
echo "  AZURE_TRANSLATOR_REGION=${LOCATION}"
