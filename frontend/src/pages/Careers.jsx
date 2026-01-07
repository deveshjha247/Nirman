import React from 'react';
import { useNavigate } from 'react-router-dom';

const RoleCard = ({ title, location, type }) => (
  <div className="p-5 rounded-2xl bg-[#111113] border border-white/5 space-y-2">
    <h3 className="text-lg font-semibold">{title}</h3>
    <p className="text-gray-400 text-sm">{location} · {type}</p>
    <button className="mt-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm hover:bg-white/10">View details</button>
  </div>
);

const Benefit = ({ title, desc }) => (
  <div className="p-4 rounded-xl bg-white/5 border border-white/10">
    <h4 className="font-semibold text-white mb-1">{title}</h4>
    <p className="text-gray-400 text-sm">{desc}</p>
  </div>
);

const Careers = () => {
  const navigate = useNavigate();

  const roles = [
    { title: 'Senior Full-stack Engineer', location: 'Remote', type: 'Full-time' },
    { title: 'Product Designer (AI)', location: 'Remote', type: 'Full-time' },
    { title: 'Developer Advocate', location: 'Remote', type: 'Full-time' },
  ];

  const benefits = [
    { title: 'Remote-first', desc: 'Work from anywhere with quarterly meetups.' },
    { title: 'Learning budget', desc: 'Annual stipend for courses, books, and events.' },
    { title: 'Health & wellness', desc: 'Comprehensive coverage and wellness stipend.' },
    { title: 'Flexible hours', desc: 'Async-friendly schedules for global teams.' },
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
            <button onClick={() => navigate('/')} className="px-4 py-2 text-sm text-gray-300 hover:text-white border border-white/10 rounded-lg">Home</button>
            <button onClick={() => navigate(-1)} className="px-4 py-2 text-sm bg-white/5 border border-white/10 rounded-lg hover:bg-white/10">Back</button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12 space-y-12">
        <section className="space-y-3">
          <p className="text-sm text-violet-300 uppercase tracking-[0.2em]">Careers</p>
          <h1 className="text-3xl md:text-4xl font-bold">Join the team</h1>
          <p className="text-gray-400 text-sm max-w-3xl">
            Help us build the next generation of AI-native development tools. We are a remote-first team that values craft, ownership, and shipping.
          </p>
        </section>

        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Open roles</h2>
            <button className="text-sm text-violet-300 hover:text-violet-200">Share your profile →</button>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {roles.map((role) => (
              <RoleCard key={role.title} {...role} />
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold">Benefits</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {benefits.map((b) => (
              <Benefit key={b.title} {...b} />
            ))}
          </div>
        </section>

        <section className="p-6 rounded-2xl bg-gradient-to-r from-violet-600/20 to-fuchsia-600/20 border border-violet-500/20">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h3 className="text-xl font-semibold">Don’t see a fit?</h3>
              <p className="text-gray-200 text-sm max-w-xl">We love hearing from curious builders. Send us your portfolio and how you’d like to contribute.</p>
            </div>
            <button className="px-5 py-3 rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 text-sm font-semibold hover:opacity-90">
              Email hiring@nirman.ai
            </button>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Careers;
