terraform {
    required_providers {
        azurerm = {
            source = "hashicorp/azurerm"
            version = "~>3.0"
        }
        tailscale = {
            source  = "tailscale/tailscale"
            version = "~> 0.15.0"
        }
    }
}

provider "azurerm" {
    features {
      
    }
}

variable "subscription" {
  type = string
}

variable "ressource_group_name" {
  type = string
}

variable "vm_name" {
  type = string
}

variable "location" {
  type = string
}

variable "size" {
  type = string
}

variable "name" {
  type = string
}

variable "admin_username" {
  type = string
}

variable "caching" {
  type = string
}

variable "storage_account_type" {
  type = string
}

variable "publisher" {
  type = string
}

variable "sku" {
  type = string
}

variable "image_version" {
  type = string
}

variable "network_interface_id" {
    type = string
}
variable "admin_password" {
    type= string
    sensitive =  true
}
variable "offer" {
    type= string
}

variable "tailscale_api_key" {
  type = string
  sensitive =  true
}

variable "tailscale_tailnet" {
  type    = string
  default = "-"
}

provider "tailscale" {
  api_key = var.tailscale_api_key
  tailnet = var.tailscale_tailnet
}

resource "azurerm_linux_virtual_machine" "existing" {
    name = var.vm_name
    resource_group_name = var.ressource_group_name
    location = var.location
    size = var.size
    admin_username = var.admin_username
    admin_password =  var.admin_password
    disable_password_authentication = false
    network_interface_ids = [var.network_interface_id]
    zone = "1" #modify this accordingly

    os_disk {
        caching = var.caching
        storage_account_type = var.storage_account_type
    }

    boot_diagnostics {
       storage_account_uri =  null
    }

    source_image_reference{
        publisher = var.publisher
        sku = var.sku
        version = var.image_version
        offer = var.offer
    }

    lifecycle {
  ignore_changes = [
    admin_ssh_key,
    admin_password,
    disable_password_authentication,
    source_image_reference,
    os_disk,
    zone,
  ]
}
}

resource "tailscale_tailnet_key" "vm_auth_key" {
  reusable  = true
  ephemeral = false
}

resource "azurerm_virtual_machine_extension" "tailscale_init" {
  name                 = "tailscale-install"
  virtual_machine_id   = azurerm_linux_virtual_machine.existing.id
  publisher            = "Microsoft.Azure.Extensions"
  type                 = "CustomScript"
  type_handler_version = "2.0"

  settings = <<SETTINGS
    {
        "commandToExecute": "curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up --authkey=${tailscale_tailnet_key.vm_auth_key.key} --hostname=${var.vm_name}"
    }
SETTINGS
}

import {
  to = azurerm_linux_virtual_machine.existing
  id = "/subscriptions/${var.subscription}/resourceGroups/${var.ressource_group_name}/providers/Microsoft.Compute/virtualMachines/${var.vm_name}"
}