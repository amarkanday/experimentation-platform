import Head from 'next/head';

export default function Home() {
  return (
    <>
      <Head>
        <title>Experimently - Modern Experimentation Platform</title>
        <meta name="description" content="The modern product experimentation platform. Ship features faster with A/B testing and feature flags." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-white">
        {/* Navigation */}
        <nav className="border-b border-gray-100 bg-white sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <div className="flex justify-between items-center h-20">
              <div className="flex items-center gap-12">
                <span className="text-2xl font-semibold text-gray-900">
                  Experimently
                </span>
                <div className="hidden lg:flex items-center gap-8">
                  <a href="#features" className="text-gray-600 hover:text-gray-900 text-sm font-medium transition">Features</a>
                  <a href="#customers" className="text-gray-600 hover:text-gray-900 text-sm font-medium transition">Customers</a>
                  <a href="#pricing" className="text-gray-600 hover:text-gray-900 text-sm font-medium transition">Pricing</a>
                  <a href="https://docs.getexperimently.com" className="text-gray-600 hover:text-gray-900 text-sm font-medium transition">Docs</a>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <a href="https://app.getexperimently.com/login" className="text-gray-600 hover:text-gray-900 text-sm font-medium">
                  Sign in
                </a>
                <a href="https://app.getexperimently.com/signup" className="bg-blue-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition">
                  Get started free
                </a>
              </div>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="pt-24 pb-16 px-6">
          <div className="max-w-5xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-full text-sm font-medium mb-8">
              <span className="w-2 h-2 bg-blue-600 rounded-full"></span>
              Now processing 1B+ events daily
            </div>
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-gray-900 mb-6 leading-tight">
              The modern product
              <br />
              experimentation platform
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 mb-10 max-w-3xl mx-auto leading-relaxed">
              Ship features faster with confidence. A/B testing, feature flags, and analytics
              for teams that move fast.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <a href="https://app.getexperimently.com/signup" className="bg-blue-600 text-white px-8 py-4 rounded-lg text-base font-semibold hover:bg-blue-700 transition shadow-sm">
                Start experimenting free
              </a>
              <a href="#demo" className="bg-white border-2 border-gray-200 text-gray-900 px-8 py-4 rounded-lg text-base font-semibold hover:border-gray-300 transition">
                See how it works
              </a>
            </div>
            <p className="text-sm text-gray-500 mt-6">Free 14-day trial · No credit card required</p>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-16 border-t border-b border-gray-100 bg-gray-50">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="text-4xl font-bold text-gray-900 mb-2">1B+</div>
                <div className="text-sm text-gray-600">Events daily</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-gray-900 mb-2">&lt;50ms</div>
                <div className="text-sm text-gray-600">P99 latency</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-gray-900 mb-2">99.99%</div>
                <div className="text-sm text-gray-600">Uptime SLA</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-gray-900 mb-2">10K+</div>
                <div className="text-sm text-gray-600">Experiments run</div>
              </div>
            </div>
          </div>
        </section>

        {/* Trusted By Section */}
        <section className="py-16 px-6">
          <div className="max-w-6xl mx-auto">
            <p className="text-center text-sm font-medium text-gray-500 mb-8">TRUSTED BY MODERN TEAMS</p>
            <div className="flex flex-wrap justify-center items-center gap-12 opacity-40">
              <div className="text-2xl font-bold text-gray-400">Acme Inc</div>
              <div className="text-2xl font-bold text-gray-400">TechCorp</div>
              <div className="text-2xl font-bold text-gray-400">StartupXYZ</div>
              <div className="text-2xl font-bold text-gray-400">DataFlow</div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-24 px-6 bg-white">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-20">
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Everything you need to experiment
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                From feature flags to advanced statistical analysis, all in one platform
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Feature 1 */}
              <div className="bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-lg hover:border-gray-200 transition">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
                  <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">A/B Testing</h3>
                <p className="text-gray-600 leading-relaxed">
                  Run multivariate experiments with statistical rigor. Built-in significance testing and confidence intervals.
                </p>
              </div>

              {/* Feature 2 */}
              <div className="bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-lg hover:border-gray-200 transition">
                <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center mb-6">
                  <svg className="w-6 h-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Feature Flags</h3>
                <p className="text-gray-600 leading-relaxed">
                  Deploy safely with gradual rollouts and targeting. Kill switch protection for instant rollback.
                </p>
              </div>

              {/* Feature 3 */}
              <div className="bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-lg hover:border-gray-200 transition">
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-6">
                  <svg className="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Real-time Analytics</h3>
                <p className="text-gray-600 leading-relaxed">
                  See results as they happen. Real-time dashboards with drill-down capabilities and custom metrics.
                </p>
              </div>

              {/* Feature 4 */}
              <div className="bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-lg hover:border-gray-200 transition">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-6">
                  <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Safety First</h3>
                <p className="text-gray-600 leading-relaxed">
                  Automated guardrails monitor error rates and performance. Auto-rollback on anomaly detection.
                </p>
              </div>

              {/* Feature 5 */}
              <div className="bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-lg hover:border-gray-200 transition">
                <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mb-6">
                  <svg className="w-6 h-6 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Advanced Targeting</h3>
                <p className="text-gray-600 leading-relaxed">
                  Target by user attributes, behavior, location, device, and custom segments with powerful rules engine.
                </p>
              </div>

              {/* Feature 6 */}
              <div className="bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-lg hover:border-gray-200 transition">
                <div className="w-12 h-12 bg-pink-100 rounded-xl flex items-center justify-center mb-6">
                  <svg className="w-6 h-6 text-pink-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Developer First</h3>
                <p className="text-gray-600 leading-relaxed">
                  SDKs for JavaScript, Python, Go, and more. RESTful APIs and comprehensive documentation.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Integration Section */}
        <section className="py-24 px-6 bg-gray-50 border-t border-gray-100">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Works with your stack
              </h2>
              <p className="text-lg text-gray-600">
                Seamlessly integrate with the tools you already use
              </p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="bg-white p-8 rounded-xl border border-gray-200 text-center">
                <div className="text-2xl font-bold text-gray-400 mb-2">AWS</div>
                <div className="text-sm text-gray-500">Cloud Infrastructure</div>
              </div>
              <div className="bg-white p-8 rounded-xl border border-gray-200 text-center">
                <div className="text-2xl font-bold text-gray-400 mb-2">Snowflake</div>
                <div className="text-sm text-gray-500">Data Warehouse</div>
              </div>
              <div className="bg-white p-8 rounded-xl border border-gray-200 text-center">
                <div className="text-2xl font-bold text-gray-400 mb-2">Segment</div>
                <div className="text-sm text-gray-500">CDP Integration</div>
              </div>
              <div className="bg-white p-8 rounded-xl border border-gray-200 text-center">
                <div className="text-2xl font-bold text-gray-400 mb-2">Slack</div>
                <div className="text-sm text-gray-500">Notifications</div>
              </div>
            </div>
          </div>
        </section>

        {/* Code Example Section */}
        <section className="py-24 px-6">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Simple to integrate
              </h2>
              <p className="text-lg text-gray-600">
                Get started in minutes with our intuitive SDKs
              </p>
            </div>
            <div className="bg-gray-900 rounded-2xl p-8 overflow-hidden">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
              </div>
              <pre className="text-sm text-gray-300 overflow-x-auto">
                <code>{`import { Experimently } from '@experimently/sdk';

const client = new Experimently('YOUR_API_KEY');

// Check if feature is enabled
const isEnabled = await client.isEnabled('new-checkout', userId);

if (isEnabled) {
  // Show new checkout flow
}

// Track conversion event
client.track('purchase_completed', userId, {
  revenue: 99.99
});`}</code>
              </pre>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-24 px-6 bg-gray-50 border-t border-gray-100">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Simple, transparent pricing
              </h2>
              <p className="text-xl text-gray-600">
                Start free, scale as you grow
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {/* Starter */}
              <div className="bg-white rounded-2xl border-2 border-gray-200 p-8">
                <div className="mb-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Starter</h3>
                  <p className="text-gray-600 mb-6">For small teams getting started</p>
                  <div className="flex items-baseline">
                    <span className="text-5xl font-bold text-gray-900">$0</span>
                    <span className="text-gray-600 ml-2">/month</span>
                  </div>
                </div>
                <ul className="space-y-4 mb-8">
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">Up to 3 experiments</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">10K events/month</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">Basic feature flags</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">Community support</span>
                  </li>
                </ul>
                <a href="https://app.getexperimently.com/signup" className="block w-full text-center bg-gray-100 text-gray-900 px-6 py-3.5 rounded-lg font-semibold hover:bg-gray-200 transition">
                  Get started
                </a>
              </div>

              {/* Pro */}
              <div className="bg-white rounded-2xl border-2 border-blue-600 p-8 relative shadow-xl">
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                  Most Popular
                </div>
                <div className="mb-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Pro</h3>
                  <p className="text-gray-600 mb-6">For growing teams</p>
                  <div className="flex items-baseline">
                    <span className="text-5xl font-bold text-gray-900">$99</span>
                    <span className="text-gray-600 ml-2">/month</span>
                  </div>
                </div>
                <ul className="space-y-4 mb-8">
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">Unlimited experiments</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">1M events/month</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">Advanced targeting</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">Priority support</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">SSO integration</span>
                  </li>
                </ul>
                <a href="https://app.getexperimently.com/signup" className="block w-full text-center bg-blue-600 text-white px-6 py-3.5 rounded-lg font-semibold hover:bg-blue-700 transition shadow-sm">
                  Start free trial
                </a>
              </div>

              {/* Enterprise */}
              <div className="bg-white rounded-2xl border-2 border-gray-200 p-8">
                <div className="mb-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Enterprise</h3>
                  <p className="text-gray-600 mb-6">For large organizations</p>
                  <div className="flex items-baseline">
                    <span className="text-5xl font-bold text-gray-900">Custom</span>
                  </div>
                </div>
                <ul className="space-y-4 mb-8">
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">Unlimited everything</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">Dedicated support</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">SLA guarantee</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">Custom contracts</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">On-premise option</span>
                  </li>
                </ul>
                <a href="mailto:hello@getexperimently.com" className="block w-full text-center bg-gray-100 text-gray-900 px-6 py-3.5 rounded-lg font-semibold hover:bg-gray-200 transition">
                  Contact sales
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-24 px-6 bg-gradient-to-br from-blue-600 to-indigo-700">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Start experimenting today
            </h2>
            <p className="text-xl text-blue-100 mb-10">
              Join thousands of teams shipping features faster with data-driven decisions
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a href="https://app.getexperimently.com/signup" className="bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-50 transition shadow-lg">
                Start free trial
              </a>
              <a href="mailto:hello@getexperimently.com" className="bg-blue-700 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-800 transition border-2 border-blue-500">
                Talk to sales
              </a>
            </div>
            <p className="text-blue-100 mt-6">14-day free trial · No credit card required</p>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-gray-900 text-white py-16 px-6">
          <div className="max-w-7xl mx-auto">
            <div className="grid md:grid-cols-5 gap-12 mb-12">
              <div className="md:col-span-2">
                <span className="text-2xl font-semibold text-white mb-4 block">
                  Experimently
                </span>
                <p className="text-gray-400 mb-6 max-w-sm">
                  The modern product experimentation platform for teams that move fast.
                </p>
                <div className="flex gap-4">
                  <a href="#" className="text-gray-400 hover:text-white transition">
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z" /></svg>
                  </a>
                  <a href="#" className="text-gray-400 hover:text-white transition">
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" /></svg>
                  </a>
                  <a href="#" className="text-gray-400 hover:text-white transition">
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" /></svg>
                  </a>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-4">Product</h4>
                <ul className="space-y-3 text-gray-400">
                  <li><a href="#features" className="hover:text-white transition">Features</a></li>
                  <li><a href="#pricing" className="hover:text-white transition">Pricing</a></li>
                  <li><a href="https://docs.getexperimently.com" className="hover:text-white transition">Documentation</a></li>
                  <li><a href="https://api.getexperimently.com" className="hover:text-white transition">API</a></li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-4">Company</h4>
                <ul className="space-y-3 text-gray-400">
                  <li><a href="#about" className="hover:text-white transition">About</a></li>
                  <li><a href="mailto:hello@getexperimently.com" className="hover:text-white transition">Contact</a></li>
                  <li><a href="#" className="hover:text-white transition">Careers</a></li>
                  <li><a href="#" className="hover:text-white transition">Blog</a></li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-4">Legal</h4>
                <ul className="space-y-3 text-gray-400">
                  <li><a href="#" className="hover:text-white transition">Privacy</a></li>
                  <li><a href="#" className="hover:text-white transition">Terms</a></li>
                  <li><a href="#" className="hover:text-white transition">Security</a></li>
                  <li><a href="mailto:support@getexperimently.com" className="hover:text-white transition">Support</a></li>
                </ul>
              </div>
            </div>

            <div className="border-t border-gray-800 pt-8">
              <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                <p className="text-gray-400 text-sm">
                  © 2025 Experimently. All rights reserved.
                </p>
                <p className="text-gray-500 text-sm">
                  Built with ❤️ for modern product teams
                </p>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
