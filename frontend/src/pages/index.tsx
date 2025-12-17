import Head from 'next/head';
import Link from 'next/link';

export default function Home() {
  return (
    <>
      <Head>
        <title>Experimently - Modern Experimentation Platform</title>
        <meta name="description" content="Run experiments that matter. A/B testing and feature flags for modern teams." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
        {/* Navigation */}
        <nav className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  Experimently
                </span>
              </div>
              <div className="hidden md:flex items-center space-x-8">
                <a href="#features" className="text-slate-600 hover:text-slate-900 transition">Features</a>
                <a href="#pricing" className="text-slate-600 hover:text-slate-900 transition">Pricing</a>
                <a href="#about" className="text-slate-600 hover:text-slate-900 transition">About</a>
                <a href="https://docs.getexperimently.com" className="text-slate-600 hover:text-slate-900 transition">Docs</a>
                <a href="https://app.getexperimently.com/login" className="text-slate-600 hover:text-slate-900 transition">Login</a>
                <a href="https://app.getexperimently.com/signup" className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-2 rounded-lg hover:shadow-lg transition">
                  Get Started
                </a>
              </div>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="relative overflow-hidden pt-20 pb-32">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h1 className="text-5xl md:text-7xl font-bold text-slate-900 mb-6">
                Run Experiments
                <br />
                <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  That Matter
                </span>
              </h1>
              <p className="text-xl md:text-2xl text-slate-600 mb-8 max-w-3xl mx-auto">
                Modern experimentation platform for A/B testing and feature flags.
                Ship features with confidence. Make data-driven decisions.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <a href="https://app.getexperimently.com/signup" className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:shadow-xl transition transform hover:scale-105">
                  Start Free Trial
                </a>
                <a href="#features" className="border-2 border-slate-300 text-slate-700 px-8 py-4 rounded-lg text-lg font-semibold hover:border-slate-400 transition">
                  See How It Works
                </a>
              </div>
              <p className="text-slate-500 mt-6">No credit card required • 14-day free trial</p>
            </div>

            {/* Hero Image/Screenshot Placeholder */}
            <div className="mt-16 relative">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-2xl p-1">
                <div className="bg-white rounded-lg p-8 min-h-96 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-8xl mb-4">📊</div>
                    <p className="text-slate-400">Dashboard Preview Coming Soon</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-20 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-slate-900 mb-4">
                Everything You Need to Experiment
              </h2>
              <p className="text-xl text-slate-600 max-w-2xl mx-auto">
                Powerful features to help you test, learn, and optimize your product
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Feature 1 */}
              <div className="p-6 border border-slate-200 rounded-xl hover:shadow-lg transition">
                <div className="text-4xl mb-4">🧪</div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">A/B Testing</h3>
                <p className="text-slate-600">
                  Run sophisticated experiments with multivariate testing, statistical analysis, and real-time results.
                </p>
              </div>

              {/* Feature 2 */}
              <div className="p-6 border border-slate-200 rounded-xl hover:shadow-lg transition">
                <div className="text-4xl mb-4">🚀</div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Feature Flags</h3>
                <p className="text-slate-600">
                  Deploy features safely with gradual rollouts, targeting rules, and instant rollback capabilities.
                </p>
              </div>

              {/* Feature 3 */}
              <div className="p-6 border border-slate-200 rounded-xl hover:shadow-lg transition">
                <div className="text-4xl mb-4">🎯</div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Advanced Targeting</h3>
                <p className="text-slate-600">
                  Target users based on attributes, behavior, segments, and custom rules with our powerful rules engine.
                </p>
              </div>

              {/* Feature 4 */}
              <div className="p-6 border border-slate-200 rounded-xl hover:shadow-lg transition">
                <div className="text-4xl mb-4">📈</div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Real-time Analytics</h3>
                <p className="text-slate-600">
                  Monitor experiment performance with real-time metrics, confidence intervals, and statistical significance.
                </p>
              </div>

              {/* Feature 5 */}
              <div className="p-6 border border-slate-200 rounded-xl hover:shadow-lg transition">
                <div className="text-4xl mb-4">🛡️</div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Safety Monitoring</h3>
                <p className="text-slate-600">
                  Automated safety checks monitor error rates and performance, with automatic rollback on issues.
                </p>
              </div>

              {/* Feature 6 */}
              <div className="p-6 border border-slate-200 rounded-xl hover:shadow-lg transition">
                <div className="text-4xl mb-4">⚡</div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Lightning Fast</h3>
                <p className="text-slate-600">
                  Sub-50ms evaluation with edge computing, intelligent caching, and optimized assignment algorithms.
                </p>
              </div>

              {/* Feature 7 */}
              <div className="p-6 border border-slate-200 rounded-xl hover:shadow-lg transition">
                <div className="text-4xl mb-4">🔐</div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Enterprise Security</h3>
                <p className="text-slate-600">
                  Role-based access control, audit logs, AWS Cognito integration, and SOC 2 compliant infrastructure.
                </p>
              </div>

              {/* Feature 8 */}
              <div className="p-6 border border-slate-200 rounded-xl hover:shadow-lg transition">
                <div className="text-4xl mb-4">🔌</div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Easy Integration</h3>
                <p className="text-slate-600">
                  SDKs for JavaScript, Python, and more. RESTful APIs and comprehensive documentation.
                </p>
              </div>

              {/* Feature 9 */}
              <div className="p-6 border border-slate-200 rounded-xl hover:shadow-lg transition">
                <div className="text-4xl mb-4">📊</div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Gradual Rollouts</h3>
                <p className="text-slate-600">
                  Progressive feature delivery with scheduled rollouts, percentage-based targeting, and rollback options.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Benefits Section */}
        <section className="py-20 bg-gradient-to-b from-slate-50 to-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <h2 className="text-4xl font-bold text-slate-900 mb-6">
                  Ship Features with Confidence
                </h2>
                <div className="space-y-6">
                  <div className="flex gap-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
                        ✓
                      </div>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-2">Reduce Risk</h3>
                      <p className="text-slate-600">
                        Test features with a small percentage of users before full rollout. Catch issues early.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
                        ✓
                      </div>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-2">Data-Driven Decisions</h3>
                      <p className="text-slate-600">
                        Make decisions based on statistical evidence, not opinions. See what actually works.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
                        ✓
                      </div>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-2">Move Faster</h3>
                      <p className="text-slate-600">
                        Decouple deployment from release. Ship code anytime, enable features when ready.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
                        ✓
                      </div>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-2">Optimize Continuously</h3>
                      <p className="text-slate-600">
                        Run experiments continuously to improve conversion, engagement, and user satisfaction.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 lg:p-12">
                <div className="text-6xl mb-4">🎯</div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">
                  Used by Modern Teams
                </h3>
                <p className="text-slate-600 mb-6">
                  Join thousands of teams using Experimently to build better products through experimentation.
                </p>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div className="bg-white rounded-lg p-4">
                    <div className="text-3xl font-bold text-blue-600">10M+</div>
                    <div className="text-sm text-slate-600">Experiments Run</div>
                  </div>
                  <div className="bg-white rounded-lg p-4">
                    <div className="text-3xl font-bold text-blue-600">&lt;50ms</div>
                    <div className="text-sm text-slate-600">P99 Latency</div>
                  </div>
                  <div className="bg-white rounded-lg p-4">
                    <div className="text-3xl font-bold text-blue-600">99.99%</div>
                    <div className="text-sm text-slate-600">Uptime</div>
                  </div>
                  <div className="bg-white rounded-lg p-4">
                    <div className="text-3xl font-bold text-blue-600">24/7</div>
                    <div className="text-sm text-slate-600">Support</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-20 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-slate-900 mb-4">
                Simple, Transparent Pricing
              </h2>
              <p className="text-xl text-slate-600 max-w-2xl mx-auto">
                Start free, scale as you grow. No hidden fees.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {/* Starter Plan */}
              <div className="border-2 border-slate-200 rounded-2xl p-8 hover:shadow-xl transition">
                <h3 className="text-2xl font-bold text-slate-900 mb-2">Starter</h3>
                <p className="text-slate-600 mb-6">Perfect for small teams and side projects</p>
                <div className="mb-6">
                  <span className="text-5xl font-bold text-slate-900">$0</span>
                  <span className="text-slate-600">/month</span>
                </div>
                <ul className="space-y-4 mb-8">
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">Up to 3 experiments</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">10K monthly events</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">Basic feature flags</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">Email support</span>
                  </li>
                </ul>
                <a href="https://app.getexperimently.com/signup" className="block w-full text-center border-2 border-slate-300 text-slate-700 px-6 py-3 rounded-lg font-semibold hover:border-slate-400 transition">
                  Get Started
                </a>
              </div>

              {/* Pro Plan */}
              <div className="border-2 border-blue-600 rounded-2xl p-8 hover:shadow-xl transition relative">
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                  Most Popular
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-2">Pro</h3>
                <p className="text-slate-600 mb-6">For growing teams and businesses</p>
                <div className="mb-6">
                  <span className="text-5xl font-bold text-slate-900">$99</span>
                  <span className="text-slate-600">/month</span>
                </div>
                <ul className="space-y-4 mb-8">
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">Unlimited experiments</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">1M monthly events</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">Advanced targeting</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">Gradual rollouts</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">Priority support</span>
                  </li>
                </ul>
                <a href="https://app.getexperimently.com/signup" className="block w-full text-center bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-3 rounded-lg font-semibold hover:shadow-lg transition">
                  Start Free Trial
                </a>
              </div>

              {/* Enterprise Plan */}
              <div className="border-2 border-slate-200 rounded-2xl p-8 hover:shadow-xl transition">
                <h3 className="text-2xl font-bold text-slate-900 mb-2">Enterprise</h3>
                <p className="text-slate-600 mb-6">For large organizations with custom needs</p>
                <div className="mb-6">
                  <span className="text-5xl font-bold text-slate-900">Custom</span>
                </div>
                <ul className="space-y-4 mb-8">
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">Everything in Pro</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">Unlimited events</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">SSO & SAML</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">Dedicated support</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-slate-600">SLA guarantee</span>
                  </li>
                </ul>
                <a href="mailto:hello@getexperimently.com" className="block w-full text-center border-2 border-slate-300 text-slate-700 px-6 py-3 rounded-lg font-semibold hover:border-slate-400 transition">
                  Contact Sales
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 bg-gradient-to-r from-blue-600 to-indigo-600">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-4xl font-bold text-white mb-6">
              Ready to Start Experimenting?
            </h2>
            <p className="text-xl text-blue-100 mb-8">
              Join thousands of teams building better products with data-driven decisions
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a href="https://app.getexperimently.com/signup" className="bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:shadow-xl transition transform hover:scale-105">
                Start Free Trial
              </a>
              <a href="mailto:hello@getexperimently.com" className="border-2 border-white text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-white hover:text-blue-600 transition">
                Contact Sales
              </a>
            </div>
            <p className="text-blue-100 mt-6">14-day free trial • No credit card required</p>
          </div>
        </section>

        {/* About Section */}
        <section id="about" className="py-20 bg-white">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-4xl font-bold text-slate-900 mb-6">
              Built for Modern Teams
            </h2>
            <p className="text-xl text-slate-600 mb-8">
              Experimently is a modern experimentation platform that helps teams make data-driven decisions
              through A/B testing and feature flags. Built on AWS with enterprise-grade security and
              performance, we help you ship features with confidence.
            </p>
            <div className="grid md:grid-cols-3 gap-8 mt-12">
              <div>
                <div className="text-4xl mb-4">🚀</div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">Fast & Reliable</h3>
                <p className="text-slate-600">
                  Sub-50ms latency with 99.99% uptime SLA
                </p>
              </div>
              <div>
                <div className="text-4xl mb-4">🔒</div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">Secure</h3>
                <p className="text-slate-600">
                  SOC 2 compliant with enterprise security
                </p>
              </div>
              <div>
                <div className="text-4xl mb-4">💡</div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">Easy to Use</h3>
                <p className="text-slate-600">
                  Simple SDKs and intuitive dashboard
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-slate-900 text-white py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid md:grid-cols-4 gap-8">
              <div>
                <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                  Experimently
                </span>
                <p className="text-slate-400 mt-4">
                  Modern experimentation platform for A/B testing and feature flags.
                </p>
              </div>

              <div>
                <h4 className="font-semibold mb-4">Product</h4>
                <ul className="space-y-2 text-slate-400">
                  <li><a href="#features" className="hover:text-white transition">Features</a></li>
                  <li><a href="#pricing" className="hover:text-white transition">Pricing</a></li>
                  <li><a href="https://docs.getexperimently.com" className="hover:text-white transition">Documentation</a></li>
                  <li><a href="https://api.getexperimently.com" className="hover:text-white transition">API Reference</a></li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold mb-4">Company</h4>
                <ul className="space-y-2 text-slate-400">
                  <li><a href="#about" className="hover:text-white transition">About</a></li>
                  <li><a href="mailto:hello@getexperimently.com" className="hover:text-white transition">Contact</a></li>
                  <li><a href="https://app.getexperimently.com/login" className="hover:text-white transition">Login</a></li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold mb-4">Support</h4>
                <ul className="space-y-2 text-slate-400">
                  <li><a href="mailto:support@getexperimently.com" className="hover:text-white transition">Help Center</a></li>
                  <li><a href="mailto:support@getexperimently.com" className="hover:text-white transition">Support</a></li>
                  <li><a href="https://docs.getexperimently.com" className="hover:text-white transition">Guides</a></li>
                </ul>
              </div>
            </div>

            <div className="border-t border-slate-800 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
              <p className="text-slate-400 text-sm">
                © 2025 Experimently. All rights reserved.
              </p>
              <div className="flex gap-6 mt-4 md:mt-0">
                <a href="mailto:hello@getexperimently.com" className="text-slate-400 hover:text-white transition">
                  Email
                </a>
                <a href="#" className="text-slate-400 hover:text-white transition">
                  Twitter
                </a>
                <a href="#" className="text-slate-400 hover:text-white transition">
                  GitHub
                </a>
              </div>
            </div>

            <div className="text-center mt-8 text-slate-500 text-sm">
              Powered by Experimently
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
