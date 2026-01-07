import React from 'react';
import { useNavigate } from 'react-router-dom';

const Stat = ({ label, value }) => (
  <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center">
    <div className="text-2xl font-bold text-white mb-1">{value}</div>
    <div className="text-gray-400 text-sm">{label}</div>
  </div>
);

const About = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <header className="border-b border-white/5 bg-[#0a0a0b]/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/') }>
            <img src="/logo.png" alt="Nirman logo" className="w-10 h-10 rounded-xl" />
            <span className="text-xl font-bold">Nirman</span>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/')} className="px-4 py-2 text-sm text-gray-300 hover:text-white border border-white/10 rounded-lg">Home</button>
            <button onClick={() => navigate(-1)} className="px-4 py-2 text-sm bg-white/5 border border-white/10 rounded-lg hover:bg-white/10">Back</button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12 space-y-12">
        <section className="space-y-3">
          <p className="text-sm text-violet-300 uppercase tracking-[0.2em]">Company</p>
          <h1 className="text-3xl md:text-4xl font-bold">About us</h1>
          <p className="text-gray-400 text-sm max-w-3xl">
            Nirman builds AI-native tools that help teams design, ship, and scale web applications faster. We combine human creativity with reliable AI systems to turn ideas into production-grade products.
          </p>
        </section>

        <section className="grid md:grid-cols-3 gap-4">
          <Stat label="Customers" value="5k+" />
          <Stat label="Uptime" value="99.9%" />
          <Stat label="Avg. build time" value="<5 min" />
        </section>

        <section className="grid md:grid-cols-2 gap-8">
          <div className="p-6 rounded-2xl bg-[#111113] border border-white/5 space-y-3">
            <h2 className="text-xl font-semibold">Our mission</h2>
            <p className="text-gray-300 text-sm leading-6">
              Empower builders everywhere to move from concept to shipped product in hours, not months. We focus on pragmatic AI that is transparent, controllable, and production-ready.
            </p>
          </div>
          <div className="p-6 rounded-2xl bg-[#111113] border border-white/5 space-y-3">
            <h2 className="text-xl font-semibold">What we value</h2>
            <ul className="list-disc list-inside text-gray-300 text-sm leading-6 space-y-1">
              <li>Shipping fast, safely</li>
              <li>Customer trust and security</li>
              <li>Clarity over hype</li>
              <li>Diverse teams, respectful debate</li>
            </ul>
          </div>
        </section>

        <section className="p-6 rounded-2xl bg-gradient-to-r from-violet-600/20 to-fuchsia-600/20 border border-violet-500/20">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h3 className="text-xl font-semibold">Join the team</h3>
              <p className="text-gray-200 text-sm max-w-xl">We hire remotely across multiple time zones. Explore open roles or reach out if you think you can help us build the future of AI tooling.</p>
            </div>
            <button
              onClick={() => navigate('/careers')}
              className="px-5 py-3 rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 text-sm font-semibold hover:opacity-90"
            >
              View careers
            </button>
          </div>
        </section>
      </main>
    </div>
  );
};

export default About;
