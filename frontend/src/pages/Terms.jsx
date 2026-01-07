import React from 'react';
import { useNavigate } from 'react-router-dom';

const Section = ({ title, children }) => (
  <section className="space-y-3">
    <h2 className="text-xl font-semibold text-white">{title}</h2>
    <div className="text-gray-300 text-sm leading-6 space-y-2">{children}</div>
  </section>
);

const Terms = () => {
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
          <p className="text-sm text-violet-300 uppercase tracking-[0.2em]">Terms</p>
          <h1 className="text-3xl md:text-4xl font-bold">Terms of Service</h1>
          <p className="text-gray-400 text-sm">Effective: Jan 3, 2026</p>
        </div>

        <div className="space-y-8">
          <Section title="1. Acceptance of terms">
            <p>By accessing or using Nirman, you agree to these Terms of Service and our Privacy Policy. If you do not agree, do not use the product.</p>
          </Section>

          <Section title="2. Service description">
            <p>Nirman provides AI-assisted tools for designing, building, and deploying web applications. Features may change as we iterate and improve.</p>
          </Section>

          <Section title="3. Accounts & security">
            <p>You are responsible for maintaining the confidentiality of your account credentials and for all activities under your account. Notify us promptly of any unauthorized use.</p>
          </Section>

          <Section title="4. Acceptable use">
            <ul className="list-disc list-inside text-gray-300 space-y-1">
              <li>No illegal, harmful, or abusive behavior.</li>
              <li>No attempts to disrupt, overload, or reverse-engineer the service.</li>
              <li>No misuse of AI outputs for harmful or deceptive purposes.</li>
            </ul>
          </Section>

          <Section title="5. Intellectual property">
            <p>We retain ownership of the platform, branding, and underlying technology. You retain ownership of your projects and content you provide, granting us the right to process it to deliver the service.</p>
          </Section>

          <Section title="6. Billing & subscriptions">
            <p>Paid plans renew automatically unless cancelled. Fees are non-refundable except where required by law. Downgrades or cancellations take effect at the end of the current billing cycle.</p>
          </Section>

          <Section title="7. AI outputs">
            <p>AI-generated content may be imperfect. Review and validate all outputs before use in production. We are not liable for decisions made based on AI suggestions.</p>
          </Section>

          <Section title="8. Termination">
            <p>We may suspend or terminate access for violations of these terms or to protect the platform. You may stop using the service at any time.</p>
          </Section>

          <Section title="9. Liability">
            <p>To the maximum extent permitted by law, Nirman is provided &quot;as is&quot; without warranties. Our liability is limited to the amount you paid in the 3 months preceding the claim.</p>
          </Section>

          <Section title="10. Changes">
            <p>We may update these terms to reflect product changes. Continued use after updates constitutes acceptance. Material changes will be communicated via the app or email.</p>
          </Section>

          <Section title="11. Contact">
            <p>Questions about these terms? Email support@nirman.ai.</p>
          </Section>
        </div>
      </main>
    </div>
  );
};

export default Terms;
