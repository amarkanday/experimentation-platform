#!/bin/bash

# Experimently Marketing Website Deployment Script
# Usage: ./deploy.sh [environment]
# Environments: dev, staging, prod

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-prod}
BUCKET_NAME="getexperimently.com"
CLOUDFRONT_DISTRIBUTION_ID=""  # Set this after creating CloudFront distribution

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Experimently Marketing Deployment${NC}"
echo -e "${BLUE}   Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if Next.js config allows static export
echo -e "\n${BLUE}📋 Checking Next.js configuration...${NC}"
if ! grep -q '"output".*"export"' next.config.js 2>/dev/null; then
    echo -e "${RED}⚠️  Next.js is not configured for static export${NC}"
    echo -e "Add this to next.config.js:"
    echo -e "  output: 'export',"
    echo -e "  images: { unoptimized: true },"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install dependencies
echo -e "\n${BLUE}📦 Installing dependencies...${NC}"
npm ci --production=false

# Build the site
echo -e "\n${BLUE}🔨 Building Next.js application...${NC}"
npm run build

# Check if build was successful
if [ ! -d "out" ]; then
    echo -e "${RED}❌ Build failed - 'out' directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build successful${NC}"

# Upload to S3
echo -e "\n${BLUE}☁️  Uploading to S3...${NC}"

# Sync static assets with long cache
echo -e "  Uploading static assets (1 year cache)..."
aws s3 sync out/ s3://${BUCKET_NAME} \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "*.html" \
  --exclude "*.json" \
  --exclude "*.txt" \
  --quiet

# Sync HTML and JSON with short cache
echo -e "  Uploading HTML/JSON files (no cache)..."
aws s3 sync out/ s3://${BUCKET_NAME} \
  --delete \
  --cache-control "public, max-age=0, must-revalidate" \
  --exclude "*" \
  --include "*.html" \
  --include "*.json" \
  --include "*.txt" \
  --quiet

echo -e "${GREEN}✅ Upload complete${NC}"

# Invalidate CloudFront cache
if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo -e "\n${BLUE}🔄 Invalidating CloudFront cache...${NC}"

    INVALIDATION_ID=$(aws cloudfront create-invalidation \
      --distribution-id ${CLOUDFRONT_DISTRIBUTION_ID} \
      --paths "/*" \
      --query 'Invalidation.Id' \
      --output text)

    echo -e "  Invalidation ID: ${INVALIDATION_ID}"
    echo -e "${GREEN}✅ Cache invalidation started${NC}"
else
    echo -e "\n${RED}⚠️  CloudFront distribution ID not set${NC}"
    echo -e "Set CLOUDFRONT_DISTRIBUTION_ID in this script to enable cache invalidation"

    # Try to find distribution automatically
    AUTO_DIST_ID=$(aws cloudfront list-distributions \
      --query "DistributionList.Items[?Aliases.Items[?contains(@, '${BUCKET_NAME}')]].Id" \
      --output text 2>/dev/null || echo "")

    if [ -n "$AUTO_DIST_ID" ]; then
        echo -e "  Found distribution: ${AUTO_DIST_ID}"
        echo -e "  Add this to the script: CLOUDFRONT_DISTRIBUTION_ID=\"${AUTO_DIST_ID}\""
    fi
fi

# Display deployment info
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "\n📊 Deployment Summary:"
echo -e "  Environment: ${ENVIRONMENT}"
echo -e "  S3 Bucket: s3://${BUCKET_NAME}"
echo -e "  Website: https://${BUCKET_NAME}"
echo -e "\n🌍 URLs:"
echo -e "  Marketing: ${GREEN}https://getexperimently.com${NC}"
echo -e "  App:       https://app.getexperimently.com"
echo -e "  API:       https://api.getexperimently.com"
echo -e "  Docs:      https://docs.getexperimently.com"

# Test deployment
echo -e "\n${BLUE}🧪 Testing deployment...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://${BUCKET_NAME} || echo "000")

if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✅ Website is live and responding${NC}"
elif [ "$HTTP_CODE" == "000" ]; then
    echo -e "${RED}⚠️  Could not connect to website${NC}"
    echo -e "   DNS may still be propagating (wait 5-10 minutes)"
else
    echo -e "${RED}⚠️  Website returned HTTP ${HTTP_CODE}${NC}"
fi

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Next steps:"
echo -e "  1. Visit https://getexperimently.com to verify"
echo -e "  2. Test on mobile devices"
echo -e "  3. Check Google PageSpeed Insights"
echo -e "  4. Set up monitoring and analytics"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
