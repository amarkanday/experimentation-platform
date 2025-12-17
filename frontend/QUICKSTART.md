# Experimently Marketing Website - Quick Start

## 🚀 Running Locally (Right Now!)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** 🎉

## 📦 What You Need

- Node.js 18+ ([Download](https://nodejs.org/))
- AWS CLI configured ([Setup Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- AWS Route 53 hosted zone for `getexperimently.com`

## ⚡ Deploy to AWS (3 Options)

### Option 1: AWS Amplify (Easiest - 5 minutes)

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize
cd frontend
amplify init

# Add hosting
amplify add hosting
# Choose: Amplify Console (Managed hosting with CI/CD)

# Publish
amplify publish
```

Then in [Amplify Console](https://console.aws.amazon.com/amplify/):
1. Add custom domain: `getexperimently.com`
2. Amplify auto-configures Route 53, SSL, and CDN
3. Done! ✅

### Option 2: Automated Script (10 minutes)

**First time setup:**

1. Update `next.config.js`:
```javascript
module.exports = {
  reactStrictMode: true,
  output: 'export',  // Add this
  images: { unoptimized: true },  // Add this
}
```

2. Create S3 bucket:
```bash
aws s3 mb s3://getexperimently.com --region us-east-1
aws s3 website s3://getexperimently.com --index-document index.html
```

3. Set up CloudFront and SSL (see [AWS_ROUTE53_DEPLOYMENT.md](../AWS_ROUTE53_DEPLOYMENT.md))

**Then deploy:**
```bash
cd frontend
./deploy.sh
```

### Option 3: Vercel (Fastest for development)

```bash
npm install -g vercel
vercel
```

Then configure Route 53 CNAME to point to Vercel.

## 🎨 Customizing the Website

All content is in **one file**: `src/pages/index.tsx`

### Change Contact Email
Find and replace:
- `hello@getexperimently.com`
- `support@getexperimently.com`

### Update Pricing
Line 273-390 in `index.tsx`

### Change Features
Line 90-172 in `index.tsx`

### Add Dashboard Screenshot
Line 65-74, replace placeholder with:
```tsx
<img src="/images/dashboard.png" alt="Dashboard" />
```

## 🔗 URLs Structure

Update these in your code when ready:

| Subdomain | Purpose | Points to |
|-----------|---------|-----------|
| `getexperimently.com` | Marketing | This Next.js site |
| `app.getexperimently.com` | Dashboard | ECS/Fargate (to build) |
| `api.getexperimently.com` | Backend API | ECS/Fargate (exists) |
| `docs.getexperimently.com` | Documentation | Static site (to build) |

## ✅ Pre-Launch Checklist

- [ ] Test site locally: `npm run dev`
- [ ] Update contact emails in code
- [ ] Add real dashboard screenshot
- [ ] Test all links (signup, login, docs, etc.)
- [ ] Add favicon to `/public/favicon.ico`
- [ ] Deploy to AWS
- [ ] Configure Route 53 DNS
- [ ] Verify SSL certificate is active
- [ ] Test from mobile device
- [ ] Run Google PageSpeed Insights
- [ ] Set up analytics (Google Analytics, Plausible, etc.)

## 🐛 Common Issues

**"Module not found" errors:**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Port 3000 in use:**
```bash
PORT=3001 npm run dev
```

**Build fails:**
```bash
rm -rf .next
npm run build
```

**Tailwind styles not working:**
- Check `tailwind.config.js` exists
- Check `globals.css` has `@tailwind` directives
- Restart dev server

## 📚 Full Documentation

- **Development Guide**: [frontend/README.md](./README.md)
- **AWS Deployment**: [AWS_ROUTE53_DEPLOYMENT.md](../AWS_ROUTE53_DEPLOYMENT.md)
- **Marketing Guide**: [MARKETING_WEBSITE_GUIDE.md](../MARKETING_WEBSITE_GUIDE.md)

## 🆘 Need Help?

1. Check [AWS_ROUTE53_DEPLOYMENT.md](../AWS_ROUTE53_DEPLOYMENT.md) for detailed AWS setup
2. Read [MARKETING_WEBSITE_GUIDE.md](../MARKETING_WEBSITE_GUIDE.md) for customization
3. Email: hello@getexperimently.com

---

**Ready to launch?** 🚀

```bash
npm run dev  # Test locally
npm run build  # Build for production
./deploy.sh  # Deploy to AWS
```
