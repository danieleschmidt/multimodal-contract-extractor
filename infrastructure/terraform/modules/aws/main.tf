# AWS Multi-Cloud Terraform Module for Multimodal Contract Extractor
# Production-ready infrastructure with comprehensive security and monitoring

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
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
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

# =============================================================================
# Variables
# =============================================================================
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod"
  }
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "mce-cluster"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "availability_zones" {
  description = "Availability zones for multi-AZ deployment"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "node_instance_types" {
  description = "EC2 instance types for EKS nodes"
  type        = list(string)
  default     = ["m5.large", "m5.xlarge", "m5.2xlarge"]
}

variable "gpu_node_instance_types" {
  description = "GPU instance types for ML workloads"
  type        = list(string)
  default     = ["p3.2xlarge", "g4dn.xlarge", "g4dn.2xlarge"]
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "contract-extractor.example.com"
}

variable "enable_gpu_nodes" {
  description = "Enable GPU node groups"
  type        = bool
  default     = true
}

variable "enable_multi_region" {
  description = "Enable multi-region deployment"
  type        = bool
  default     = false
}

variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 30
}

variable "monitoring_retention_days" {
  description = "Monitoring data retention period in days"
  type        = number
  default     = 90
}

# =============================================================================
# Data Sources
# =============================================================================
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

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
# KMS Keys for Encryption
# =============================================================================
resource "aws_kms_key" "mce_key" {
  description             = "KMS key for MCE encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow use of the key for EKS"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_kms_alias" "mce_key" {
  name          = "alias/mce-${var.environment}-${random_string.suffix.result}"
  target_key_id = aws_kms_key.mce_key.key_id
}

# =============================================================================
# VPC and Networking
# =============================================================================
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = [for i, az in var.availability_zones : cidrsubnet(var.vpc_cidr, 8, i + 1)]
  public_subnets  = [for i, az in var.availability_zones : cidrsubnet(var.vpc_cidr, 8, i + 101)]
  database_subnets = [for i, az in var.availability_zones : cidrsubnet(var.vpc_cidr, 8, i + 201)]

  enable_nat_gateway   = true
  enable_vpn_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  # Flow logs for security monitoring
  enable_flow_log                      = true
  create_flow_log_cloudwatch_log_group = true
  create_flow_log_cloudwatch_iam_role  = true
  flow_log_destination_type            = "cloud-watch-logs"
  
  # Network ACLs for additional security
  manage_default_network_acl = true
  default_network_acl_ingress = [
    {
      rule_no    = 100
      action     = "allow"
      from_port  = 0
      to_port    = 0
      protocol   = "-1"
      cidr_block = var.vpc_cidr
    }
  ]
  
  default_network_acl_egress = [
    {
      rule_no    = 100
      action     = "allow"
      from_port  = 0
      to_port    = 0
      protocol   = "-1"
      cidr_block = "0.0.0.0/0"
    }
  ]

  # Subnet tags for EKS
  public_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                     = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"           = "1"
  }

  database_subnet_tags = {
    "Database" = "true"
  }

  tags = local.common_tags
}

# =============================================================================
# Security Groups
# =============================================================================

# EKS Cluster Security Group
resource "aws_security_group" "eks_cluster" {
  name_prefix = "${var.cluster_name}-cluster-"
  vpc_id      = module.vpc.vpc_id
  
  description = "Security group for EKS cluster control plane"

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.cluster_name}-cluster-sg"
  })
}

# Database Security Group
resource "aws_security_group" "database" {
  name_prefix = "${var.cluster_name}-db-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for RDS database"

  ingress {
    description     = "PostgreSQL from EKS nodes"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.cluster_name}-database-sg"
  })
}

# Cache Security Group
resource "aws_security_group" "cache" {
  name_prefix = "${var.cluster_name}-cache-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for ElastiCache"

  ingress {
    description     = "Redis from EKS nodes"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  tags = merge(local.common_tags, {
    Name = "${var.cluster_name}-cache-sg"
  })
}

# EKS Nodes Security Group
resource "aws_security_group" "eks_nodes" {
  name_prefix = "${var.cluster_name}-nodes-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for EKS worker nodes"

  ingress {
    description = "Node to node communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description     = "Control plane to nodes"
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster.id]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.cluster_name}-nodes-sg"
  })
}

# =============================================================================
# EKS Cluster
# =============================================================================
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.28"

  vpc_config {
    subnet_ids              = concat(module.vpc.private_subnets, module.vpc.public_subnets)
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
    security_group_ids      = [aws_security_group.eks_cluster.id]
  }

  # Enable logging for security and compliance
  enabled_cluster_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]

  # Encryption at rest
  encryption_config {
    provider {
      key_arn = aws_kms_key.mce_key.arn
    }
    resources = ["secrets"]
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller,
    aws_cloudwatch_log_group.eks_cluster
  ]

  tags = local.common_tags
}

# CloudWatch Log Group for EKS
resource "aws_cloudwatch_log_group" "eks_cluster" {
  name              = "/aws/eks/${var.cluster_name}/cluster"
  retention_in_days = var.monitoring_retention_days
  kms_key_id        = aws_kms_key.mce_key.arn

  tags = local.common_tags
}

# =============================================================================
# EKS Node Groups
# =============================================================================

# CPU Node Group
resource "aws_eks_node_group" "cpu_nodes" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "cpu-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = module.vpc.private_subnets

  instance_types = var.node_instance_types
  capacity_type  = "SPOT"
  ami_type       = "AL2_x86_64"

  scaling_config {
    desired_size = 3
    max_size     = 10
    min_size     = 2
  }

  update_config {
    max_unavailable_percentage = 25
  }

  # Advanced configuration
  disk_size = 100

  remote_access {
    ec2_ssh_key               = aws_key_pair.eks_nodes.key_name
    source_security_group_ids = [aws_security_group.eks_nodes.id]
  }

  labels = {
    role        = "cpu-worker"
    environment = var.environment
    node-type   = "compute-optimized"
  }

  taint {
    key    = "node-type"
    value  = "cpu"
    effect = "NO_SCHEDULE"
  }

  tags = merge(local.common_tags, {
    Name = "${var.cluster_name}-cpu-nodes"
  })

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
  ]
}

# GPU Node Group (conditional)
resource "aws_eks_node_group" "gpu_nodes" {
  count = var.enable_gpu_nodes ? 1 : 0
  
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "gpu-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = module.vpc.private_subnets

  instance_types = var.gpu_node_instance_types
  capacity_type  = "ON_DEMAND"  # GPU instances work better with On-Demand
  ami_type       = "AL2_x86_64_GPU"

  scaling_config {
    desired_size = 1
    max_size     = 5
    min_size     = 0
  }

  update_config {
    max_unavailable_percentage = 25
  }

  disk_size = 200  # Larger disk for GPU workloads

  labels = {
    role        = "gpu-worker"
    environment = var.environment
    node-type   = "gpu-optimized"
  }

  taint {
    key    = "nvidia.com/gpu"
    value  = "true"
    effect = "NO_SCHEDULE"
  }

  tags = merge(local.common_tags, {
    Name = "${var.cluster_name}-gpu-nodes"
  })

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
  ]
}

# SSH Key Pair for EKS Nodes
resource "tls_private_key" "eks_nodes" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "eks_nodes" {
  key_name   = "${var.cluster_name}-nodes-key"
  public_key = tls_private_key.eks_nodes.public_key_openssh

  tags = local.common_tags
}

# Store private key in AWS Secrets Manager
resource "aws_secretsmanager_secret" "eks_ssh_key" {
  name                    = "${var.cluster_name}-ssh-private-key"
  description             = "SSH private key for EKS nodes"
  kms_key_id              = aws_kms_key.mce_key.arn
  recovery_window_in_days = 7

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "eks_ssh_key" {
  secret_id     = aws_secretsmanager_secret.eks_ssh_key.id
  secret_string = tls_private_key.eks_nodes.private_key_pem
}

# =============================================================================
# Common Tags
# =============================================================================
locals {
  common_tags = {
    Environment     = var.environment
    Project         = "multimodal-contract-extractor"
    Terraform       = "true"
    CreatedBy       = "terraform"
    Owner           = "mce-team"
    CostCenter      = "research-ai"
    BackupRequired  = "true"
    MonitoringLevel = "production"
    SecurityLevel   = "high"
    ComplianceLevel = "enterprise"
    Region          = var.region
    Cluster         = var.cluster_name
  }
}