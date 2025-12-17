# Experimently Marketing Website - Quick Start Guide

## What We Built

A modern, professional marketing website for Experimently with:

✅ **Landing Page** with hero section and "Run Experiments That Matter" tagline
✅ **Features Section** showcasing 9 key platform capabilities
✅ **Benefits Section** with value propositions and stats
✅ **Pricing Section** with 3 tiers (Starter, Pro, Enterprise)
✅ **About Section** explaining the platform
✅ **Professional Navigation** with smooth scrolling
✅ **Footer** with all contact information and links
✅ **Responsive Design** using Tailwind CSS
✅ **Branding** following Experimently style guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the marketing site.

### 3. Build for Production

```bash
npm run build
npm run start
```

## 📧 Branding & Contact Info

**All contact information is already configured:**

- **General Contact**: hello@getexperimently.com
- **Support**: support@getexperimently.com
- **Domain**: getexperimently.com
- **App**: app.getexperimently.com
- **API**: api.getexperimently.com
- **Docs**: docs.getexperimently.com

## 🎨 Design System

**Colors:**
- Primary Gradient: Blue (#2563eb) to Indigo (#4f46e5)
- Text: Slate-900 for headings, Slate-600 for body
- Background: White with Slate-50 for alternating sections

**Typography:**
- System font stack optimized for readability
- Responsive sizing (mobile to desktop)

## 📄 Page Sections

### 1. Hero Section
- Main headline: "Run Experiments That Matter"
- Tagline about A/B testing and feature flags
- Two CTAs: "Start Free Trial" and "See How It Works"
- Placeholder for dashboard screenshot

### 2. Features Grid (9 Features)
- A/B Testing
- Feature Flags
- Advanced Targeting
- Real-time Analytics
- Safety Monitoring
- Lightning Fast Performance
- Enterprise Security
- Easy Integration
- Gradual Rollouts

### 3. Benefits Section
- "Ship Features with Confidence" headline
- 4 key benefits with checkmarks
- Stats card with metrics

### 4. Pricing Tiers
- **Starter**: $0/month (3 experiments, 10K events)
- **Pro**: $99/month (unlimited experiments, 1M events) - Most Popular
- **Enterprise**: Custom pricing with all features

### 5. CTA Section
- Strong call-to-action in blue gradient background
- "Ready to Start Experimenting?" headline
- Trial and contact sales CTAs

### 6. About Section
- Company description
- 3 value propositions

### 7. Footer
- 4-column layout with links
- Product, Company, Support sections
- Social links placeholder
- Copyright and "Powered by Experimently"

## 🔧 Customization Guide

### Update Statistics

Edit `/frontend/src/pages/index.tsx` around line 250-267:

```tsx
<div className="text-3xl font-bold text-blue-600">10M+</div>
<div className="text-sm text-slate-600">Experiments Run</div>
```

### Update Pricing

Edit `/frontend/src/pages/index.tsx` starting at line 273:

```tsx
<div className="mb-6">
  <span className="text-5xl font-bold text-slate-900">$99</span>
  <span className="text-slate-600">/month</span>
</div>
```

### Add Dashboard Screenshot

Replace the placeholder (line 65-74) with:

```tsx
<div className="mt-16 relative">
  <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-2xl p-1">
    <img
      src="/images/dashboard-screenshot.png"
      alt="Experimently Dashboard"
      className="rounded-lg"
    />
  </div>
</div>
```

### Update Contact Email

Search and replace in `/frontend/src/pages/index.tsx`:
- `hello@getexperimently.com` → your general email
- `support@getexperimently.com` → your support email

## 🌐 Deployment Options

### Option 1: Vercel (Recommended)

1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import your repository
4. Set root directory to `frontend`
5. Deploy!

Vercel will automatically:
- Build your Next.js app
- Set up SSL certificate
- Configure CDN
- Enable automatic deployments

### Option 2: AWS Amplify

1. Go to AWS Amplify Console
2. Connect your repository
3. Set build settings:
   - Build command: `npm run build`
   - Output directory: `.next`
4. Deploy

### Option 3: Static Hosting (Netlify, CloudFront + S3)

```bash
npm run build
# Upload .next/out folder to your hosting
```

## 📱 Mobile Responsiveness

The site is fully responsive with breakpoints:
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

Test responsive design:
- Chrome DevTools (Cmd+Option+I)
- Resize browser window
- Use real devices

## 🎯 Next Steps

### Immediate (Before Launch)
1. ✅ Add real dashboard screenshot to hero
2. ✅ Connect signup/login to actual backend
3. ✅ Test all links and forms
4. ✅ Add favicon and social media images
5. ✅ Set up domain and SSL

### Short Term
1. Add customer testimonials section
2. Create blog/resources page
3. Implement contact form with backend
4. Add newsletter signup
5. Set up analytics (Google Analytics, Plausible, etc.)

### Long Term
1. Add case studies page
2. Create interactive product demos
3. Build documentation site
4. Add integration examples
5. Create video tutorials

## 🔍 SEO Optimization

The page already has:
- ✅ Proper title and meta description
- ✅ Semantic HTML structure
- ✅ Heading hierarchy (H1, H2, H3)
- ✅ Alt text for images (ready for when you add images)

**Still needed:**
- [ ] Add Open Graph tags for social sharing
- [ ] Create sitemap.xml
- [ ] Add robots.txt
- [ ] Optimize image sizes
- [ ] Add structured data (JSON-LD)

## 📊 Analytics Setup

### Google Analytics

Add to `/frontend/src/pages/_app.tsx`:

```tsx
import Script from 'next/script'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Script
        src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"
        strategy="afterInteractive"
      />
      <Script id="google-analytics" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'GA_MEASUREMENT_ID');
        `}
      </Script>
      <Component {...pageProps} />
    </>
  )
}
```

## 🐛 Troubleshooting

**Issue: Tailwind styles not working**
```bash
# Make sure dependencies are installed
npm install

# Check tailwind.config.js exists
# Check globals.css has @tailwind directives
```

**Issue: Build fails**
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

**Issue: Port 3000 already in use**
```bash
# Use different port
PORT=3001 npm run dev
```

## 📞 Support

Questions? Contact: hello@getexperimently.com

---

Built with ❤️ using Next.js 14 and Tailwind CSS
