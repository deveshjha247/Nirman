import React from 'react';
import { useNavigate } from 'react-router-dom';

const Section = ({ title, children }) => (
  <section className="space-y-3">
    <h2 className="text-xl font-semibold text-white">{title}</h2>
    <div className="text-gray-300 text-sm leading-6 space-y-2">{children}</div>
  </section>
);

const Privacy = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <header className="border-b border-white/5 bg-[#0a0a0b]/80 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
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

      <main className="max-w-5xl mx-auto px-6 py-12 space-y-10">
        <div className="space-y-3">
          <p className="text-sm text-violet-300 uppercase tracking-[0.2em]">Privacy</p>
          <h1 className="text-3xl md:text-4xl font-bold">Privacy Policy</h1>
          <p className="text-gray-400 text-sm">Effective: Jan 3, 2026</p>
        </div>

        <div className="space-y-8">
          <Section title="1. Data we collect">
            <ul className="list-disc list-inside text-gray-300 space-y-1">
              <li>Account data: name, email, authentication details.</li>
              <li>Usage data: app interactions, logs, device and browser info.</li>
              <li>Content data: prompts, project assets, and files you upload.</li>
            </ul>
          </Section>

          <Section title="2. How we use data">
            <p>We use data to operate, secure, and improve Nirman; to personalize experiences; to provide support; and to communicate updates or billing notices.</p>
          </Section>

          <Section title="3. AI processing">
            <p>Your prompts and project context may be sent to third-party AI providers (e.g., OpenAI, Google, Anthropic) to generate outputs. Do not submit sensitive personal data in prompts.</p>
          </Section>

          <Section title="4. Cookies & tracking">
            <p>We use essential cookies for security and session management, and optional analytics/marketing cookies when you opt in. Manage preferences anytime at /cookies.</p>
          </Section>

          <Section title="5. Sharing">
            <p>We do not sell personal data. We may share data with infrastructure, analytics, and AI vendors under contract, and when required by law or to protect users and the platform.</p>
          </Section>

          <Section title="6. Retention">
            <p>We retain data while your account is active and as needed to provide the service. Backups and logs are kept for a limited period for security and compliance.</p>
          </Section>

          <Section title="7. Security">
            <p>We apply industry-standard security controls, encryption in transit, and access controls. No system is perfectly secure; report issues to security@nirman.ai.</p>
          </Section>

          <Section title="8. Your choices">
            <ul className="list-disc list-inside text-gray-300 space-y-1">
              <li>Access, update, or delete your account data via settings or support.</li>
              <li>Manage cookies at /cookies and email preferences via links in messages.</li>
              <li>Opt out of marketing communications at any time.</li>
            </ul>
          </Section>

          <Section title="9. International transfers">
            <p>Data may be processed globally with safeguards such as SCCs or similar measures where applicable.</p>
          </Section>

          <Section title="10. Changes">
            <p>We may update this policy to reflect product or regulatory changes. Continued use after updates indicates acceptance; material updates will be notified in-app or by email.</p>
          </Section>

          <Section title="11. Contact">
            <p>Questions about privacy? Email privacy@nirman.ai.</p>
          </Section>
        </div>
      </main>
    </div>
  );
};

export default Privacy;
