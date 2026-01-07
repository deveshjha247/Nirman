import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { referralsAPI } from '../lib/api';
import Sidebar from '../components/Sidebar';

const Referrals = () => {
  const { user } = useAuth();
  const [referralData, setReferralData] = useState(null);
  const [copied, setCopied] = useState(false);

  const fetchReferrals = async () => {
    try {
      const response = await referralsAPI.getReferrals();
      setReferralData(response.data);
    } catch (error) {
      console.error('Failed to fetch referrals:', error);
    }
  };

  useEffect(() => {
    fetchReferrals();
  }, []);

  const copyLink = () => {
    navigator.clipboard.writeText(referralData?.referral_link || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white flex">
      <Sidebar active="referrals" />
      
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold mb-8">Referral Program</h1>
        
        {/* Referral Stats */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
            <p className="text-gray-400 mb-2">Your Referral Code</p>
            <h3 className="text-2xl font-bold text-violet-400">{referralData?.referral_code}</h3>
          </div>
          <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
            <p className="text-gray-400 mb-2">Total Referrals</p>
            <h3 className="text-2xl font-bold">{referralData?.total_referrals || 0}</h3>
          </div>
          <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
            <p className="text-gray-400 mb-2">Total Earnings</p>
            <h3 className="text-2xl font-bold text-green-400">₹{referralData?.total_earnings || 0}</h3>
          </div>
        </div>
        
        {/* Share Link */}
        <div className="bg-gradient-to-r from-violet-600/20 to-fuchsia-600/20 border border-violet-500/30 rounded-2xl p-6 mb-8">
          <h3 className="text-lg font-semibold mb-2">Share Your Link & Earn ₹50!</h3>
          <p className="text-gray-400 mb-4">When your friend makes their first purchase, you get ₹50 in your wallet and they get 10% off!</p>
          <div className="flex gap-4">
            <input
              type="text"
              value={referralData?.referral_link || ''}
              readOnly
              className="flex-1 px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white"
            />
            <button
              onClick={copyLink}
              className="px-6 py-3 bg-violet-600 rounded-xl font-semibold hover:bg-violet-700 transition-colors"
            >
              {copied ? 'Copied!' : 'Copy Link'}
            </button>
          </div>
        </div>
        
        {/* Referrals List */}
        <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
          <h3 className="text-lg font-semibold mb-4">Your Referrals</h3>
          {referralData?.referrals?.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No referrals yet. Share your link to start earning!</p>
          ) : (
            <div className="space-y-3">
              {referralData?.referrals?.map((ref, i) => (
                <div key={ref.id || i} className="flex items-center justify-between p-4 bg-[#0a0a0b] rounded-xl">
                  <div>
                    <p className="font-medium">{ref.referee_name || ref.referee_email}</p>
                    <p className="text-sm text-gray-500">{new Date(ref.created_at).toLocaleDateString()}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm ${ref.bonus_given ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                    {ref.bonus_given ? `+₹${ref.bonus_amount}` : 'Pending'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Referrals;
