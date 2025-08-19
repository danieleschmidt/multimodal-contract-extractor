# Google Cloud Platform Infrastructure for Multimodal Contract Extractor
# Production-ready multi-cloud deployment with GKE and comprehensive services

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

# =============================================================================
# Variables
# =============================================================================
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "zones" {
  description = "GCP zones for multi-zone deployment"
  type        = list(string)
  default     = ["us-central1-a", "us-central1-b", "us-central1-c"]
}

variable "cluster_name" {
  description = "GKE cluster name"
  type        = string
  default     = "mce-cluster"
}

variable "network_name" {
  description = "VPC network name"
  type        = string
  default     = "mce-network"
}

variable "subnet_cidr" {
  description = "Subnet CIDR range"
  type        = string
  default     = "10.1.0.0/16"
}

variable "pods_cidr" {
  description = "Pod IP range"
  type        = string
  default     = "10.2.0.0/16"
}

variable "services_cidr" {
  description = "Services IP range"
  type        = string
  default     = "10.3.0.0/16"
}

variable "node_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-standard-4"
}

variable "gpu_node_machine_type" {
  description = "Machine type for GPU nodes"
  type        = string
  default     = "n1-standard-4"
}

variable "gpu_type" {
  description = "GPU type for ML workloads"
  type        = string
  default     = "nvidia-tesla-t4"
}

variable "enable_gpu_nodes" {
  description = "Enable GPU node pool"
  type        = bool
  default     = true
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "contract-extractor.example.com"
}

# =============================================================================
# Random Resources
# =============================================================================
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "random_password" "redis_password" {
  length  = 32
  special = false
}

# =============================================================================
# Enable Required APIs
# =============================================================================
resource "google_project_service" "required_apis" {
  for_each = toset([
    "container.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudkms.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "clouddebugger.googleapis.com",
    "cloudprofiler.googleapis.com",
    "storage.googleapis.com",
    "dns.googleapis.com",
    "certificatemanager.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "artifactregistry.googleapis.com"
  ])

  service = each.value
  project = var.project_id

  disable_dependent_services = false
  disable_on_destroy         = false
}

# =============================================================================
# KMS Keys for Encryption
# =============================================================================
resource "google_kms_key_ring" "mce_keyring" {
  name     = "mce-keyring-${random_string.suffix.result}"
  location = var.region
  project  = var.project_id

  depends_on = [google_project_service.required_apis]
}

resource "google_kms_crypto_key" "mce_key" {
  name     = "mce-key"
  key_ring = google_kms_key_ring.mce_keyring.id
  
  purpose          = "ENCRYPT_DECRYPT"
  rotation_period  = "7776000s"  # 90 days

  lifecycle {
    prevent_destroy = true
  }

  labels = local.common_labels
}

# =============================================================================
# VPC Network and Subnets
# =============================================================================
resource "google_compute_network" "vpc" {
  name                    = var.network_name
  auto_create_subnetworks = false
  mtu                     = 1460
  project                 = var.project_id

  depends_on = [google_project_service.required_apis]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${var.network_name}-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
  project       = var.project_id

  # Secondary IP ranges for GKE
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.services_cidr
  }

  # Enable private Google access
  private_ip_google_access = true

  # Enable flow logs for security monitoring
  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# =============================================================================
# Cloud Router and NAT Gateway
# =============================================================================
resource "google_compute_router" "router" {
  name    = "${var.network_name}-router"
  region  = var.region
  network = google_compute_network.vpc.id
  project = var.project_id

  bgp {
    asn = 64514
  }
}

resource "google_compute_router_nat" "nat" {
  name                               = "${var.network_name}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  project                            = var.project_id
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# =============================================================================
# Firewall Rules
# =============================================================================

# Allow internal communication
resource "google_compute_firewall" "allow_internal" {
  name    = "${var.network_name}-allow-internal"
  network = google_compute_network.vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
  }

  allow {
    protocol = "udp"
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = [var.subnet_cidr, var.pods_cidr, var.services_cidr]
}

# Allow health checks
resource "google_compute_firewall" "allow_health_checks" {
  name    = "${var.network_name}-allow-health-checks"
  network = google_compute_network.vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["8080", "8501", "8502"]
  }

  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  target_tags   = ["gke-node"]
}

# Allow SSH for debugging (restrict in production)
resource "google_compute_firewall" "allow_ssh" {
  name    = "${var.network_name}-allow-ssh"
  network = google_compute_network.vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]  # IAP range
  target_tags   = ["gke-node"]
}

# =============================================================================
# GKE Service Account
# =============================================================================
resource "google_service_account" "gke_service_account" {
  account_id   = "${var.cluster_name}-gke-sa"
  display_name = "GKE Service Account for MCE"
  project      = var.project_id
}

resource "google_project_iam_member" "gke_service_account_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer",
    "roles/storage.objectViewer",
    "roles/artifactregistry.reader"
  ])

  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_service_account.email}"
  project = var.project_id
}

# =============================================================================
# GKE Cluster
# =============================================================================
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.region
  project  = var.project_id

  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1

  # Network configuration
  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

  # IP allocation policy for VPC-native networking
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"

    master_global_access_config {
      enabled = true
    }
  }

  # Master authorized networks
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "All networks"
    }
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Enable network policy
  network_policy {
    enabled = true
  }

  # Add-ons configuration
  addons_config {
    http_load_balancing {
      disabled = false
    }

    horizontal_pod_autoscaling {
      disabled = false
    }

    network_policy_config {
      disabled = false
    }

    dns_cache_config {
      enabled = true
    }

    gce_persistent_disk_csi_driver_config {
      enabled = true
    }

    gcp_filestore_csi_driver_config {
      enabled = true
    }
  }

  # Enable logging and monitoring
  logging_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "WORKLOADS",
      "API_SERVER"
    ]
  }

  monitoring_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "WORKLOADS",
      "APISERVER",
      "SCHEDULER",
      "CONTROLLER_MANAGER"
    ]

    managed_prometheus {
      enabled = true
    }
  }

  # Binary authorization
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }

  # Security configuration
  enable_shielded_nodes = true

  # Database encryption
  database_encryption {
    state    = "ENCRYPTED"
    key_name = google_kms_crypto_key.mce_key.id
  }

  # Pod security policy (deprecated but still supported)
  pod_security_policy_config {
    enabled = false
  }

  # Maintenance policy
  maintenance_policy {
    recurring_window {
      start_time = "2023-01-01T03:00:00Z"
      end_time   = "2023-01-01T07:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SU"
    }
  }

  # Notification configuration
  notification_config {
    pubsub {
      enabled = true
      topic   = google_pubsub_topic.gke_notifications.id
    }
  }

  depends_on = [
    google_project_service.required_apis,
    google_compute_subnetwork.subnet
  ]
}

# =============================================================================
# Node Pools
# =============================================================================

# CPU Node Pool
resource "google_container_node_pool" "cpu_nodes" {
  name       = "cpu-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  project    = var.project_id
  node_count = 1

  # Auto-scaling configuration
  autoscaling {
    min_node_count = 1
    max_node_count = 10
  }

  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }

  # Node configuration
  node_config {
    preemptible  = true
    machine_type = var.node_machine_type
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    # Google service account
    service_account = google_service_account.gke_service_account.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    # Shielded instance config
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    # Labels and tags
    labels = merge(local.common_labels, {
      node-type = "cpu"
    })

    tags = ["gke-node", "cpu-node"]

    # Metadata
    metadata = {
      disable-legacy-endpoints = "true"
    }

    # Taints
    taint {
      key    = "node-type"
      value  = "cpu"
      effect = "NO_SCHEDULE"
    }
  }

  # Node pool management
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# GPU Node Pool
resource "google_container_node_pool" "gpu_nodes" {
  count = var.enable_gpu_nodes ? 1 : 0

  name       = "gpu-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  project    = var.project_id
  node_count = 0

  # Auto-scaling configuration
  autoscaling {
    min_node_count = 0
    max_node_count = 5
  }

  # Node configuration
  node_config {
    preemptible  = false  # GPU nodes should be on-demand
    machine_type = var.gpu_node_machine_type
    disk_size_gb = 200
    disk_type    = "pd-ssd"

    # GPU configuration
    guest_accelerator {
      type  = var.gpu_type
      count = 1
    }

    # Google service account
    service_account = google_service_account.gke_service_account.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    # Labels and tags
    labels = merge(local.common_labels, {
      node-type = "gpu"
    })

    tags = ["gke-node", "gpu-node"]

    # Metadata
    metadata = {
      disable-legacy-endpoints = "true"
    }

    # Taints for GPU scheduling
    taint {
      key    = "nvidia.com/gpu"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
  }

  # Node pool management
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# =============================================================================
# Common Labels
# =============================================================================
locals {
  common_labels = {
    environment   = var.environment
    project       = "multimodal-contract-extractor"
    managed-by    = "terraform"
    team          = "mce-team"
    cost-center   = "research-ai"
    region        = var.region
    cluster       = var.cluster_name
  }
}

# =============================================================================
# Pub/Sub Topic for Notifications
# =============================================================================
resource "google_pubsub_topic" "gke_notifications" {
  name    = "${var.cluster_name}-notifications"
  project = var.project_id

  labels = local.common_labels

  depends_on = [google_project_service.required_apis]
}