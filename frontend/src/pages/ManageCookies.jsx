import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const ManageCookies = () => {
  const navigate = useNavigate();
  const [prefs, setPrefs] = useState({
    essential: true,
    analytics: true,
    personalization: false,
    marketing: false,
  });
  const [status, setStatus] = useState('');

  const toggle = (key) => {
    if (key === 'essential') return; // essential cookies cannot be disabled
    setPrefs((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = () => {
    setStatus('Preferences saved.');
    setTimeout(() => setStatus(''), 2000);
  };

  const handleReset = () => {
    setPrefs({ essential: true, analytics: true, personalization: false, marketing: false });
    setStatus('Preferences reset to defaults.');
    setTimeout(() => setStatus(''), 2000);
  };

  const sections = [
    {
      title: 'Product',
      links: ['Pricing', 'Web app', 'AI design', 'AI slides', 'Wide Research', 'Slack integration'],
    },
    {
      title: 'Resources',
      links: ['Blog', 'Docs', 'Updates', 'Help center', 'Trust center', 'API', 'Team plan', 'Startups', 'Playbook', 'Brand assets'],
    },
    {
      title: 'Community',
      links: ['Events', 'Campus', 'Fellows'],
    },
    {
      title: 'Compare',
      links: ['VS Others', 'VS Competitors'],
    },
    {
      title: 'Download',
      links: ['Mobile app', 'Windows app', 'My Browser'],
    },
    {
      title: 'Company',
      links: ['About us', 'Careers', 'For business', 'For media', 'Terms of service', 'Privacy policy', 'Manage cookies'],
    },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <header className="border-b border-white/5 bg-[#0a0a0b]/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/') }>
            <img src="/logo.png" alt="Nirman logo" className="w-10 h-10 rounded-xl" />
            <span className="text-xl font-bold">Nirman</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 text-sm text-gray-300 hover:text-white border border-white/10 rounded-lg"
            >
              Home
            </button>
            <button
              onClick={() => navigate(-1)}
              className="px-4 py-2 text-sm bg-white/5 border border-white/10 rounded-lg hover:bg-white/10"
            >
              Back
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12 space-y-10">
        <section>
          <div className="flex items-start justify-between gap-6 flex-col md:flex-row md:items-center">
            <div>
              <p className="text-sm text-violet-300 uppercase tracking-[0.2em] mb-3">Privacy controls</p>
              <h1 className="text-3xl md:text-4xl font-bold mb-4">Manage cookies & preferences</h1>
              <p className="text-gray-400 max-w-2xl">
                Adjust how we use cookies to improve your experience. Essential cookies keep the product secure and cannot be turned off.
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleReset}
                className="px-4 py-2 rounded-lg border border-white/10 text-sm text-gray-200 hover:bg-white/5"
              >
                Reset
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 text-sm font-semibold hover:opacity-90"
              >
                Save preferences
              </button>
            </div>
          </div>
          {status && <p className="mt-4 text-sm text-green-400">{status}</p>}
        </section>

        <section className="grid md:grid-cols-2 gap-6">
          {[{
            key: 'essential',
            title: 'Essential',
            desc: 'Required for security, authentication, and basic functionality.',
          }, {
            key: 'analytics',
            title: 'Analytics',
            desc: 'Helps us understand usage to improve performance.',
          }, {
            key: 'personalization',
            title: 'Personalization',
            desc: 'Tailors content and recommendations to your activity.',
          }, {
            key: 'marketing',
            title: 'Marketing',
            desc: 'Used for measuring campaigns and showing relevant offers.',
          }].map(({ key, title, desc }) => (
            <div key={key} className="p-6 bg-[#111113] border border-white/5 rounded-2xl flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold mb-2">{title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{desc}</p>
                {key === 'essential' && <p className="text-xs text-violet-300 mt-2">Always enabled</p>}
              </div>
              <button
                className={`relative inline-flex h-7 w-12 items-center rounded-full border border-white/10 transition-all ${
                  prefs[key] ? 'bg-violet-600' : 'bg-white/10'
                } ${key === 'essential' ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
                onClick={() => toggle(key)}
                aria-pressed={prefs[key]}
                disabled={key === 'essential'}
              >
                <span
                  className={`inline-block h-5 w-5 rounded-full bg-white transform transition-transform ${
                    prefs[key] ? 'translate-x-5' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          ))}
        </section>

        <section>
          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="text-sm text-violet-300 uppercase tracking-[0.2em] mb-2">Explore</p>
              <h2 className="text-2xl font-semibold">All product areas</h2>
              <p className="text-gray-400 text-sm">Browse key areas of the platform from one place.</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sections.map((section) => (
              <div key={section.title} className="p-6 bg-[#111113] border border-white/5 rounded-2xl">
                <h3 className="font-semibold text-white mb-4">{section.title}</h3>
                <ul className="space-y-2.5">
                  {section.links.map((item) => (
                    <li key={item}>
                      <a href="#" className="text-gray-400 hover:text-white transition-colors text-sm flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-violet-500"></span>
                        {item}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
};

export default ManageCookies;
