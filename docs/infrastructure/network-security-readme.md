# Network Security Configuration

## Overview

This Terraform configuration sets up a robust network infrastructure with comprehensive security measures:

### Key Components
- Virtual Private Cloud (VPC)
- Public and Private Subnets
- NAT Gateways
- Security Groups
- Network Access Control Lists (NACLs)

## Security Group Configuration

### Web Server Security Group
- Allows inbound traffic on ports 80 (HTTP) and 443 (HTTPS)
- Permits all outbound traffic
- Provides basic web server access controls

### Database Security Group
- Restricts database access to web servers only
- Limits inbound access to PostgreSQL port (5432)
- Prevents direct external database access

## NAT Gateway Setup

- Two NAT Gateways for high availability
- One NAT Gateway per availability zone
- Enables private subnets to access internet securely
- Uses Elastic IPs for stable external access

## Network ACL Configuration

### Public Subnet ACL
- Allows inbound HTTP, HTTPS, and SSH traffic
- Permits all outbound traffic
- Provides additional layer of network-level security

### Private Subnet ACL
- Restricts inbound traffic to VPC CIDR block
- Allows outbound traffic to all destinations
- Adds an extra security layer for internal resources

## Deployment Considerations

- Customize CIDR blocks as per your network design
- Adjust security group and ACL rules to match specific requirements
- Consider implementing additional security measures like VPC endpoints

## Prerequisites

- AWS Account
- Terraform installed
- AWS CLI configured

## Deployment Instructions

```bash
# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply configuration
terraform apply
```

## Security Best Practices

- Regularly audit and update security group rules
- Implement principle of least privilege
- Use strong network segmentation
- Monitor and log network traffic
