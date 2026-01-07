import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const urlReferralCode = searchParams.get('ref');
  const [referralCode, setReferralCode] = useState(urlReferralCode || '');
  const [showReferralInput, setShowReferralInput] = useState(!urlReferralCode);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(email, name, password, referralCode || null);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50/30 via-white to-purple-50/30 flex items-center justify-center p-6 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-20 left-20 w-96 h-96 bg-purple-200/30 rounded-full blur-3xl animate-float"></div>
        <div className="absolute bottom-20 right-20 w-80 h-80 bg-violet-200/30 rounded-full blur-3xl animate-float-delayed"></div>
      </div>

      <div className="w-full max-w-md relative z-10">
        <div className="bg-white/90 backdrop-blur-xl p-10 rounded-3xl shadow-2xl shadow-purple-200/30 border border-purple-100">
          <div className="text-center mb-10">
            <img src="/logo.png" alt="Nirman Logo" className="w-16 h-16 mx-auto rounded-xl shadow-lg shadow-purple-300/50 mb-8" />
            <h1 className="text-3xl font-bold text-gray-900 mb-3">Create account</h1>
            <p className="text-gray-600 text-lg">Start building with AI today</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm font-medium" data-testid="register-error">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2.5">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-5 py-3.5 bg-gray-50 border border-purple-100 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 focus:bg-white transition-all"
                placeholder="John Doe"
                required
                data-testid="register-name-input"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-5 py-3.5 bg-gray-50 border border-purple-100 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 focus:bg-white transition-all"
                placeholder="you@example.com"
                required
                data-testid="register-email-input"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-5 py-3.5 bg-gray-50 border border-purple-100 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 focus:bg-white transition-all"
                placeholder="••••••••"
                required
                minLength={6}
                data-testid="register-password-input"
              />
            </div>

            {/* Referral Code Section */}
            <div>
              {referralCode && !showReferralInput ? (
                <div className="flex items-center justify-between p-3.5 bg-green-50 border border-green-200 rounded-xl">
                  <div className="flex items-center gap-2">
                    <span className="text-green-600">✓</span>
                    <span className="text-green-700 text-sm font-medium">Referral: <strong>{referralCode}</strong> (10% off!)</span>
                  </div>
                  <button type="button" onClick={() => setShowReferralInput(true)} className="text-gray-500 hover:text-purple-600 text-sm font-medium">Change</button>
                </div>
              ) : (
                <div>
                  <div className="flex items-center justify-between mb-2.5">
                    <label className="block text-sm font-semibold text-gray-700">Referral Code (Optional)</label>
                    {referralCode && <span className="text-green-600 text-xs font-semibold">✓ Applied</span>}
                  </div>
                  <input
                    type="text"
                    value={referralCode}
                    onChange={(e) => setReferralCode(e.target.value.toUpperCase())}
                    className="w-full px-5 py-3.5 bg-gray-50 border border-purple-100 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 focus:bg-white transition-all"
                    placeholder="Enter referral code"
                    maxLength={8}
                    data-testid="register-referral-input"
                  />
                  {referralCode && <p className="text-green-600 text-sm mt-2 font-medium">🎉 You&apos;ll get 10% off on your first purchase!</p>}
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-violet-700 transition-all shadow-lg shadow-purple-300/50 hover:shadow-xl hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 active:scale-95"
              data-testid="register-submit-btn"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <p className="text-center text-gray-600 mt-8 text-sm">
            Already have an account?{' '}
            <button onClick={() => navigate('/login')} className="text-purple-600 hover:text-purple-700 font-semibold transition-colors" data-testid="goto-login-btn">
              Sign in
            </button>
          </p>
        </div>

        <button onClick={() => navigate('/')} className="block mx-auto mt-8 text-gray-500 hover:text-purple-600 transition-colors text-sm font-medium">
          ← Back to home
        </button>
      </div>
    </div>
  );
};

export default Register;
