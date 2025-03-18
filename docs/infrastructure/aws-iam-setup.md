# AWS IAM User Setup for Experimentation Platform

This guide outlines the process for creating an AWS IAM user with the appropriate permissions needed to build and deploy the experimentation platform infrastructure.

## Creating the IAM User

### Step 1: Create the User

1. Log in to the AWS Management Console
2. Navigate to the IAM service
3. Click on "Users" in the left navigation pane
4. Click "Create user"
5. Enter a username: `experimentation-platform-developer`
6. Select "Access key - Programmatic access" for AWS CLI/SDK access
7. Select "Password - AWS Management Console access" if console access is needed
8. Click "Next: Permissions"

### Step 2: Set Permissions

#### Option A: Using AWS Managed Policies

Attach these AWS managed policies:

- `AmazonRDSFullAccess` (for Aurora PostgreSQL)
- `AmazonDynamoDBFullAccess` (for DynamoDB tables)
- `AmazonElastiCacheFullAccess` (for Redis)
- `AmazonECS-FullAccess` (for ECS containers)
- `AmazonEC2ContainerRegistryFullAccess` (for ECR)
- `AWSLambda_FullAccess` (for Lambda functions)
- `AmazonKinesisFullAccess` (for Kinesis streams)
- `AmazonAPIGatewayAdministrator` (for API Gateway)
- `AmazonS3FullAccess` (for S3 storage)
- `AmazonVPCFullAccess` (for networking)
- `CloudWatchFullAccess` (for monitoring)
- `IAMFullAccess` (for service roles)
- `AWSCloudFormationFullAccess` (for CDK deployments)

#### Option B: Custom Policy (Recommended for Production)

Create a custom policy with more precise permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "iam:PassRole",
        "iam:GetRole",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "ec2:*",
        "elasticloadbalancing:*",
        "rds:*",
        "dynamodb:*",
        "elasticache:*",
        "lambda:*",
        "apigateway:*",
        "s3:*",
        "ecs:*",
        "ecr:*",
        "logs:*",
        "cloudwatch:*",
        "kinesis:*",
        "cognito-idp:*",
        "es:*",
        "kms:*",
        "secretsmanager:*",
        "ssm:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 3: Add Tags

Add organizational tags:
- Key: `Project`, Value: `ExperimentationPlatform`
- Key: `Role`, Value: `Developer`
- Key: `ManagedBy`, Value: `IAC`

### Step 4: Review and Create

1. Review the permissions
2. Click "Create user"
3. Download or save the access key ID and secret access key

## Configuring AWS CLI

Set up the AWS CLI with the new credentials:

```bash
aws configure --profile experimentation-platform
```

Enter:
- AWS Access Key ID: [your access key]
- AWS Secret Access Key: [your secret key]
- Default region name: us-east-1 (or your preferred region)
- Default output format: json

## Using with AWS CDK

When using the AWS CDK, specify the profile:

```bash
cdk deploy --profile experimentation-platform
```

Or set it as an environment variable:

```bash
export AWS_PROFILE=experimentation-platform
cdk deploy
```

## CDK Bootstrap

Bootstrap the AWS environment for CDK (needs to be done once per account/region):

```bash
cdk bootstrap aws://ACCOUNT-NUMBER/REGION --profile experimentation-platform
```

## Security Best Practices

1. **Use the Principle of Least Privilege**: In production, further refine the policy to include only the specific resources needed
2. **Enable MFA**: For additional security, enable multi-factor authentication
3. **Rotate Access Keys