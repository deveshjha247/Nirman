import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { plansAPI } from '../lib/api';

const Landing = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [plans, setPlans] = useState([]);
  const [promptInput, setPromptInput] = useState('');

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const response = await plansAPI.getPlans();
        setPlans(response.data);
      } catch (error) {
        console.error('Failed to fetch plans:', error);
      }
    };
    fetchPlans();
  }, []);

  const handlePromptSubmit = (e) => {
    e.preventDefault();
    if (user) {
      navigate(`/dashboard?prompt=${encodeURIComponent(promptInput)}`);
    } else {
      navigate('/register');
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-2xl border-b border-purple-100/50 shadow-lg shadow-purple-100/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="Nirman Logo" className="w-11 h-11 rounded-xl shadow-lg shadow-purple-300/50" />
            <span className="text-xl font-bold text-gray-900">Nirman</span>
          </div>
          <div className="hidden md:flex items-center gap-10">
            <a href="#features" className="text-gray-600 hover:text-purple-600 transition-colors text-sm font-medium">Features</a>
            <a href="#pricing" className="text-gray-600 hover:text-purple-600 transition-colors text-sm font-medium">Pricing</a>
            <a href="/about" className="text-gray-600 hover:text-purple-600 transition-colors text-sm font-medium">About</a>
          </div>
          <div className="flex items-center gap-3">
            {user ? (
              <button
                onClick={() => navigate('/dashboard')}
                className="px-7 py-3 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-violet-700 transition-all shadow-lg shadow-purple-300/50 hover:shadow-xl hover:scale-105"
                data-testid="dashboard-btn"
              >
                Dashboard
              </button>
            ) : (
              <>
                <button onClick={() => navigate('/login')} className="px-6 py-3 text-gray-600 hover:text-purple-600 transition-colors font-medium" data-testid="login-btn">Sign in</button>
                <button onClick={() => navigate('/register')} className="px-7 py-3 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-violet-700 transition-all shadow-lg shadow-purple-300/50 hover:shadow-xl hover:scale-105" data-testid="register-btn">Get Started</button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-24 px-6 overflow-hidden bg-gradient-to-b from-purple-50/30 via-white to-white">
        {/* Animated background gradients */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-10 w-96 h-96 bg-purple-200/20 rounded-full blur-3xl animate-float"></div>
          <div className="absolute top-40 right-10 w-80 h-80 bg-violet-200/20 rounded-full blur-3xl animate-float-delayed"></div>
          <div className="absolute bottom-20 left-1/2 w-72 h-72 bg-fuchsia-200/20 rounded-full blur-3xl animate-float-slow"></div>
        </div>
        
        <div className="relative z-10 max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/90 backdrop-blur-sm border border-purple-100 rounded-full mb-10 shadow-lg shadow-purple-100/50">
            <span className="w-2 h-2 rounded-full bg-gradient-to-r from-purple-500 to-violet-500 animate-pulse"></span>
            <span className="text-sm text-gray-700 font-medium">Powered by GPT-4, Gemini & Claude</span>
          </div>

          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold text-gray-900 mb-8 leading-[1.05] tracking-tight">
            What can I build<br />
            <span className="text-gradient-purple">for you?</span>
          </h1>

          <p className="text-xl md:text-2xl text-gray-600 mb-14 max-w-2xl mx-auto leading-relaxed">
            Describe your idea and watch AI bring it to life. Build websites, apps, and more with natural language.
          </p>

          {/* Main Prompt Input */}
          <form onSubmit={handlePromptSubmit} className="max-w-3xl mx-auto mb-10">
            <div className="relative group">
              <input
                type="text"
                value={promptInput}
                onChange={(e) => setPromptInput(e.target.value)}
                placeholder="Build a landing page for my SaaS product..."
                className="w-full px-7 py-6 bg-white/90 backdrop-blur-sm border border-purple-100 rounded-2xl text-gray-900 text-lg placeholder-gray-400 shadow-2xl shadow-purple-100/20 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 focus:shadow-2xl transition-all duration-300 pr-36 group-hover:border-purple-200 group-hover:shadow-purple-200/30"
              />
              <button
                type="submit"
                className="absolute right-3 top-1/2 -translate-y-1/2 px-7 py-3 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-violet-700 transition-all duration-200 shadow-lg shadow-purple-300/50 hover:shadow-xl hover:shadow-purple-400/50 hover:scale-105 active:scale-95"
              >
                Create
              </button>
            </div>
          </form>

          {/* Quick Action Chips */}
          <div className="flex flex-wrap justify-center gap-3 mb-20">
            {[
              { icon: '📊', text: 'Create slides' },
              { icon: '🌐', text: 'Build website' },
              { icon: '📱', text: 'Develop apps' },
              { icon: '🎨', text: 'Design' },
              { icon: '✨', text: 'More' }
            ].map((action, i) => (
              <button
                key={i}
                onClick={() => setPromptInput(action.text === 'More' ? '' : `${action.text} for my project`)}
                className="px-6 py-3 bg-white/90 backdrop-blur-sm border border-purple-100/80 hover:border-purple-200 hover:shadow-xl hover:shadow-purple-100/30 hover:-translate-y-0.5 text-gray-700 hover:text-purple-700 rounded-full text-sm font-medium transition-all duration-200 flex items-center gap-2.5 shadow-lg shadow-gray-100/50"
              >
                <span className="text-lg">{action.icon}</span>
                {action.text}
              </button>
            ))}
          </div>

          {/* Template Showcase */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5 max-w-4xl mx-auto">
            {[
              { title: 'Custom Web Tool', desc: 'Build calculators & converters', img: '🛠️' },
              { title: 'Landing Page', desc: 'High-converting pages', img: '📄' },
              { title: 'Portfolio', desc: 'Showcase your work', img: '🎯' },
              { title: 'Dashboard', desc: 'Data visualization', img: '📊' }
            ].map((template, i) => (
              <div 
                key={i} 
                onClick={() => navigate(user ? '/dashboard' : '/register')}
                className="p-5 bg-white/90 backdrop-blur-sm border border-purple-100/80 rounded-2xl hover:border-purple-200 hover:shadow-2xl hover:shadow-purple-100/30 hover:-translate-y-1 transition-all duration-300 cursor-pointer group"
              >
                <div className="text-4xl mb-4 group-hover:scale-125 transition-transform duration-300">{template.img}</div>
                <h3 className="font-semibold text-gray-900 text-sm mb-1.5">{template.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{template.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-28 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-5">Powerful Features</h2>
            <p className="text-gray-600 text-lg md:text-xl max-w-2xl mx-auto">Everything you need to bring your ideas to life</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              { icon: '🤖', title: 'Multi-AI Support', desc: 'Choose from GPT-4, Gemini, or Claude for code generation' },
              { icon: '⚡', title: 'Instant Preview', desc: 'See your changes in real-time as AI generates code' },
              { icon: '🎨', title: 'Modern UI', desc: 'Beautiful, responsive designs with Tailwind CSS' },
              { icon: '📁', title: 'Project Management', desc: 'Save, organize, and manage all your projects' },
              { icon: '💬', title: 'Chat Interface', desc: 'Natural conversation to refine your app' },
              { icon: '🚀', title: 'Export Ready', desc: 'Download production-ready code instantly' }
            ].map((feature, i) => (
              <div key={i} className="p-8 bg-white/90 backdrop-blur-sm border border-purple-100/80 rounded-2xl hover:border-purple-200 hover:shadow-2xl hover:shadow-purple-100/20 hover:-translate-y-1 transition-all duration-300 group">
                <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-violet-100 rounded-2xl flex items-center justify-center text-4xl mb-6 group-hover:scale-110 group-hover:rotate-3 transition-transform duration-300">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-28 px-6 bg-gradient-to-b from-white to-purple-50/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-5">Simple, Transparent Pricing</h2>
            <p className="text-gray-600 text-lg md:text-xl max-w-2xl mx-auto">Choose the plan that works for you</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {plans.map((plan) => (
              <div key={plan.id} className={`p-8 rounded-3xl border transition-all duration-500 ${plan.id === 'pro'
                ? 'bg-gradient-to-br from-purple-600 via-violet-600 to-purple-700 border-purple-500 text-white shadow-2xl shadow-purple-300/50 scale-105 hover:scale-110'
                : 'bg-white/90 backdrop-blur-sm border-purple-100 hover:border-purple-200 hover:shadow-2xl hover:shadow-purple-100/20 hover:-translate-y-1'
                }`}>
                {plan.id === 'pro' && (
                  <div className="text-center mb-6">
                    <span className="px-4 py-2 bg-white/20 backdrop-blur-sm text-white text-xs font-bold tracking-wider rounded-full uppercase shadow-lg">Most Popular</span>
                  </div>
                )}
                <h3 className={`text-2xl font-bold mb-3 ${plan.id === 'pro' ? 'text-white' : 'text-gray-900'}`}>{plan.name}</h3>
                <div className="mb-8 flex items-baseline gap-2">
                  <span className={`text-5xl font-bold ${plan.id === 'pro' ? 'text-white' : 'text-gray-900'}`}>₹{plan.price_monthly}</span>
                  <span className={plan.id === 'pro' ? 'text-purple-100' : 'text-gray-500'}>/month</span>
                </div>

                <ul className="space-y-4 mb-8">
                  {plan.features?.map((feature, fi) => (
                    <li key={fi} className={`flex items-start gap-3 ${plan.id === 'pro' ? 'text-purple-50' : 'text-gray-600'}`}>
                      <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center mt-0.5 ${plan.id === 'pro' ? 'bg-white/20 text-white' : 'bg-gradient-to-br from-purple-100 to-violet-100 text-purple-600'}`}>
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M11 4L5.5 9.5L3 7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
                      </span>
                      <span className="leading-relaxed">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => navigate(user ? '/plans' : '/register')}
                  className={`w-full py-4 rounded-xl font-semibold transition-all duration-200 shadow-lg ${plan.id === 'pro'
                    ? 'bg-white text-purple-600 hover:bg-purple-50 hover:scale-105 shadow-white/30'
                    : 'bg-gradient-to-r from-purple-600 to-violet-600 text-white hover:from-purple-700 hover:to-violet-700 hover:scale-105 shadow-purple-300/50'
                    }`}
                >
                  {plan.price_monthly === 0 ? 'Start Free' : 'Get Started'}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-16 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          {/* Footer Navigation Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 mb-12">
            {/* Product */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Product</h3>
              <ul className="space-y-2.5">
                <li><a href="#pricing" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Pricing</a></li>
                <li><a href="/dashboard" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Web app</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">AI design</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">AI slides</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Wide Research</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Slack integration</a></li>
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Resources</h3>
              <ul className="space-y-2.5">
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Blog</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Docs</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Updates</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Help center</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Trust center</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">API</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Team plan</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Startups</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Playbook</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Brand assets</a></li>
              </ul>
            </div>

            {/* Community */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Community</h3>
              <ul className="space-y-2.5">
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Events</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Campus</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Fellows</a></li>
              </ul>
            </div>

            {/* Compare */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Compare</h3>
              <ul className="space-y-2.5">
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">VS Others</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">VS Competitors</a></li>
              </ul>
            </div>

            {/* Download */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Download</h3>
              <ul className="space-y-2.5">
                <li><a href="/download#mobile" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Mobile app</a></li>
                <li><a href="/download#windows" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Windows app</a></li>
                <li><a href="/download#web" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">My Browser</a></li>
              </ul>
            </div>

            {/* Company */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Company</h3>
              <ul className="space-y-2.5">
                <li><a href="/about" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">About us</a></li>
                <li><a href="/careers" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Careers</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">For business</a></li>
                <li><a href="#" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">For media</a></li>
                <li><a href="/terms" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Terms of service</a></li>
                <li><a href="/privacy" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Privacy policy</a></li>
                <li><a href="/cookies" className="text-gray-500 hover:text-gray-900 transition-colors text-sm">Manage cookies</a></li>
              </ul>
            </div>
          </div>

          {/* Footer Bottom */}
          <div className="pt-8 border-t border-gray-200 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-gray-500 text-sm">© 2026 Nirman AI · Singapore</p>

            <div className="flex items-center gap-4">
              {/* Social Media Icons */}
              <a href="#" className="text-gray-400 hover:text-gray-900 transition-colors" aria-label="LinkedIn">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-gray-900 transition-colors" aria-label="Twitter">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-gray-900 transition-colors" aria-label="YouTube">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z" />
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-gray-900 transition-colors" aria-label="Instagram">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-gray-900 transition-colors" aria-label="TikTok">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z" />
                </svg>
              </a>

              <div className="h-4 w-px bg-gray-200 mx-1"></div>

              <a href="#" className="text-gray-400 hover:text-gray-900 transition-colors" aria-label="Language">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                </svg>
              </a>
              <span className="text-gray-500 text-sm">English</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
