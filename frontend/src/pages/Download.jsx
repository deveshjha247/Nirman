import React from 'react';
import { useNavigate } from 'react-router-dom';

const Download = () => {
  const navigate = useNavigate();

  const cards = [
    {
      id: 'mobile',
      title: 'Mobile app',
      desc: 'Build and monitor on the go with our iOS & Android app.',
      cta: 'Join mobile beta',
    },
    {
      id: 'windows',
      title: 'Windows app',
      desc: 'Native desktop experience with faster previews and offline drafts.',
      cta: 'Download for Windows',
    },
    {
      id: 'web',
      title: 'My Browser',
      desc: 'Use Nirman instantly from any modern browser—no install required.',
      cta: 'Open web app',
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
            <button onClick={() => navigate('/')} className="px-4 py-2 text-sm text-gray-300 hover:text-white border border-white/10 rounded-lg">Home</button>
            <button onClick={() => navigate(-1)} className="px-4 py-2 text-sm bg-white/5 border border-white/10 rounded-lg hover:bg-white/10">Back</button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12 space-y-10">
        <section className="space-y-3">
          <p className="text-sm text-violet-300 uppercase tracking-[0.2em]">Download</p>
          <h1 className="text-3xl md:text-4xl font-bold">Get Nirman on every device</h1>
          <p className="text-gray-400 text-sm max-w-3xl">
            Choose the experience that fits you best—mobile for quick edits, desktop for deep work, or web for instant access.
          </p>
        </section>

        <section className="grid md:grid-cols-3 gap-6">
          {cards.map((card) => (
            <div key={card.id} id={card.id} className="p-6 rounded-2xl bg-[#111113] border border-white/5 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">{card.title}</h2>
                <span className="text-xs px-3 py-1 rounded-full bg-white/5 border border-white/10 text-gray-300">Beta</span>
              </div>
              <p className="text-gray-300 text-sm leading-6">{card.desc}</p>
              <button className="w-full px-4 py-3 rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 text-sm font-semibold hover:opacity-90">
                {card.cta}
              </button>
            </div>
          ))}
        </section>

        <section className="p-6 rounded-2xl bg-gradient-to-r from-violet-600/20 to-fuchsia-600/20 border border-violet-500/20">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h3 className="text-xl font-semibold">Need enterprise installers?</h3>
              <p className="text-gray-200 text-sm max-w-xl">Get MSI/EXE packages, silent install scripts, and managed updates for your org.</p>
            </div>
            <button className="px-5 py-3 rounded-lg bg-white/10 border border-white/20 text-sm font-semibold hover:bg-white/15">
              Contact sales
            </button>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Download;
