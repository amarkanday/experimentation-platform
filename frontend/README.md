# Experimently - Marketing Website

This is the marketing website for Experimently, a modern experimentation platform for A/B testing and feature flags.

## Tech Stack

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Deployment**: Vercel (recommended)

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install

# Run the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to see the marketing website.

### Build for Production

```bash
# Create production build
npm run build

# Start production server
npm run start
```

## Project Structure

```
frontend/
├── src/
│   ├── pages/           # Next.js pages
│   │   ├── index.tsx    # Marketing landing page
│   │   ├── _app.tsx     # App wrapper
│   │   └── ...          # Other pages
│   └── styles/
│       └── globals.css  # Global styles with Tailwind
├── public/              # Static assets
├── tailwind.config.js   # Tailwind configuration
├── tsconfig.json        # TypeScript configuration
└── package.json
```

## Marketing Website Features

The landing page includes:

- **Hero Section**: Main headline with CTA buttons
- **Features Grid**: 9 key features with icons and descriptions
- **Benefits Section**: Value propositions with stats
- **Pricing Section**: Three-tier pricing (Starter, Pro, Enterprise)
- **CTA Section**: Strong call-to-action with trial offer
- **About Section**: Company information
- **Footer**: Links and contact information

## Branding

- **Brand Name**: Experimently
- **Domain**: getexperimently.com
- **Tagline**: "Run experiments that matter"
- **Color Scheme**: Blue (#2563eb) to Indigo (#4f46e5) gradient
- **Email**:
  - General: hello@getexperimently.com
  - Support: support@getexperimently.com

## Subdomain Structure

- **Marketing**: getexperimently.com (this site)
- **App**: app.getexperimently.com (application dashboard)
- **API**: api.getexperimently.com (API endpoints)
- **Docs**: docs.getexperimently.com (documentation)

## Deployment

### Vercel (Recommended)

1. Connect your GitHub repository to Vercel
2. Set the root directory to `frontend`
3. Deploy

### Manual Deployment

```bash
npm run build
npm run start
```

## Environment Variables

No environment variables are required for the marketing site. All links point to the appropriate subdomains.

## Customization

### Update Contact Information

Edit `/src/pages/index.tsx` and search for:
- `hello@getexperimently.com` - General contact
- `support@getexperimently.com` - Support contact

### Update Pricing

Edit the pricing section in `/src/pages/index.tsx` starting around line 273.

### Update Features

Edit the features grid in `/src/pages/index.tsx` starting around line 90.

## Next Steps

1. Add real dashboard screenshot to hero section
2. Connect to actual signup/login pages when backend is ready
3. Add blog/resources section
4. Implement contact form
5. Add customer testimonials
6. Set up analytics (Google Analytics, Mixpanel, etc.)
7. Add SEO optimizations (meta tags, sitemap, robots.txt)

## Support

For questions or issues, contact: hello@getexperimently.com
