terraform {
  required_version = ">= 1.6.0, < 2.0.0"
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = ">= 1.50.0, < 2.0.0"
    }
  }
  # Configure a protected remote backend for a real environment before apply.
}

provider "hcloud" {} # Uses HCLOUD_TOKEN; never put its value in this file.

variable "name" {
  type = string
}
variable "server_type" {
  type = string
}
variable "location" {
  type = string
}
variable "image" {
  type = string
}
variable "ssh_key_ids" {
  type = list(string)
  validation {
    condition     = length(var.ssh_key_ids) > 0
    error_message = "Provide existing public SSH key IDs."
  }
}
variable "admin_cidrs" {
  type = list(string)
  validation {
    condition = length(var.admin_cidrs) > 0 && alltrue([
      for cidr in var.admin_cidrs : can(cidrhost(cidr, 0)) && !endswith(cidr, "/0")
    ])
    error_message = "Use valid restricted admin CIDRs, never a default route."
  }
}
variable "ssh_port" {
  type    = number
  default = 22
  validation {
    condition     = var.ssh_port >= 1 && var.ssh_port <= 65535 && floor(var.ssh_port) == var.ssh_port
    error_message = "SSH port must be an integer from 1 to 65535."
  }
}

resource "hcloud_firewall" "web" {
  name = "${var.name}-edge"
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = tostring(var.ssh_port)
    source_ips = var.admin_cidrs
  }
  dynamic "rule" {
    for_each = toset(["80", "443"])
    content {
      direction  = "in"
      protocol   = "tcp"
      port       = rule.value
      source_ips = ["0.0.0.0/0", "::/0"]
    }
  }
  rule {
    direction  = "in"
    protocol   = "icmp"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
  # No outbound restriction here. Adapt egress to the reviewed flow matrix.
}

resource "hcloud_server" "node" {
  name         = var.name
  server_type  = var.server_type
  location     = var.location
  image        = var.image
  ssh_keys     = var.ssh_key_ids
  firewall_ids = [hcloud_firewall.web.id]
  backups      = true
  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }
  lifecycle {
    prevent_destroy = true
  }
}

output "ipv4_address" {
  value = hcloud_server.node.ipv4_address
}
