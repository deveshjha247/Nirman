import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { plansAPI } from '../lib/api';
import Sidebar from '../components/Sidebar';

const Plans = () => {
  const { user, refreshUser } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [billingCycle, setBillingCycle] = useState('monthly');
  const [couponCode, setCouponCode] = useState('');
  const [couponError, setCouponError] = useState('');
  const [couponDiscount, setCouponDiscount] = useState(0);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await plansAPI.getPlans();
      setPlans(response.data);
    } catch (error) {
      console.error('Failed to fetch plans:', error);
    }
  };

  const validateCoupon = async (planId, amount) => {
    if (!couponCode.trim()) {
      setCouponError('');
      setCouponDiscount(0);
      return true;
    }

    try {
      const response = await plansAPI.validateCoupon(couponCode, planId, amount);
      setCouponDiscount(response.data.discount);
      setCouponError('');
      return true;
    } catch (error) {
      setCouponError(error.response?.data?.detail || 'Invalid coupon');
      setCouponDiscount(0);
      return false;
    }
  };

  const purchasePlan = async (planId) => {
    if (planId === 'free') return;

    const plan = plans.find(p => p.id === planId);
    const amount = billingCycle === 'yearly' ? plan.price_yearly : plan.price_monthly;

    if (couponCode && !(await validateCoupon(planId, amount))) {
      return;
    }

    setLoading(true);
    try {
      const response = await plansAPI.purchase(planId, billingCycle, true, couponCode || null);

      if (response.data.status === 'success') {
        const msg = response.data.discount > 0
          ? `Plan purchased successfully! You saved ₹${response.data.discount}`
          : 'Plan purchased successfully!';
        alert(msg);
        refreshUser();
        setCouponCode('');
        setCouponDiscount(0);
      } else if (response.data.status === 'payment_required') {
        alert(`Please add ₹${response.data.amount} to your wallet to purchase this plan.`);
      }
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to purchase plan');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50/30 via-white to-purple-50/30 flex">
      <Sidebar active="plans" />

      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">Choose Your Plan</h1>
            <p className="text-gray-600 text-lg">
              Current Plan: <span className="text-purple-600 font-semibold">{user?.plan?.toUpperCase()}</span>
            </p>
          </div>

          {/* Coupon Code Input */}
          <div className="max-w-md mx-auto mb-12">
            <div className="bg-white/90 backdrop-blur-sm border border-purple-100 rounded-2xl p-6 shadow-xl shadow-purple-100/20">
              <label className="block text-sm font-semibold text-gray-700 mb-3">Have a coupon code?</label>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={couponCode}
                  onChange={(e) => { setCouponCode(e.target.value.toUpperCase()); setCouponError(''); setCouponDiscount(0); }}
                  placeholder="Enter coupon code"
                  className="flex-1 px-5 py-3.5 bg-gray-50 border border-purple-100 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 focus:bg-white transition-all"
                  data-testid="coupon-code-input"
                />
              </div>
              {couponError && <p className="text-red-600 text-sm mt-3 flex items-center gap-2 font-medium"><span>⚠️</span> {couponError}</p>}
              {couponDiscount > 0 && <p className="text-green-600 text-sm mt-3 flex items-center gap-2 font-medium"><span>🎉</span> Coupon applied! You&apos;ll save ₹{couponDiscount}</p>}
            </div>
          </div>

          {/* Billing Toggle */}
          <div className="flex justify-center mb-16">
            <div className="bg-white/90 backdrop-blur-sm p-2 rounded-xl flex items-center border border-purple-100 shadow-lg shadow-purple-100/20">
              <button
                onClick={() => setBillingCycle('monthly')}
                className={`px-8 py-3 rounded-xl font-semibold transition-all duration-300 ${billingCycle === 'monthly' ? 'bg-gradient-to-r from-purple-600 to-violet-600 text-white shadow-lg shadow-purple-300/50' : 'text-gray-600 hover:text-purple-600'}`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingCycle('yearly')}
                className={`px-8 py-3 rounded-xl font-semibold transition-all duration-300 flex items-center gap-2 ${billingCycle === 'yearly' ? 'bg-gradient-to-r from-purple-600 to-violet-600 text-white shadow-lg shadow-purple-300/50' : 'text-gray-600 hover:text-purple-600'}`}
              >
                Yearly <span className="text-xs font-bold text-green-600 bg-green-100 px-2 py-0.5 rounded-full uppercase tracking-wider">Save 20%</span>
              </button>
            </div>
          </div>

          {/* Plans */}
          <div className="grid md:grid-cols-3 gap-8">
            {plans.map((plan) => (
              <div key={plan.id} className={`p-8 rounded-3xl border transition-all duration-500 ${plan.id === user?.plan
                ? 'border-purple-300 bg-purple-50 hover:shadow-2xl hover:shadow-purple-200/30'
                : plan.id === 'pro'
                  ? 'bg-gradient-to-br from-purple-600 via-violet-600 to-purple-700 border-purple-500 text-white shadow-2xl shadow-purple-300/50 hover:scale-105'
                  : 'bg-white/90 backdrop-blur-sm border-purple-100 hover:border-purple-200 hover:shadow-2xl hover:shadow-purple-100/20 hover:-translate-y-1'
                }`}>

                {plan.id === user?.plan && (
                  <div className="text-center mb-6">
                    <span className="px-4 py-2 bg-purple-100 text-purple-700 border border-purple-200 text-xs font-bold rounded-full uppercase tracking-wider">Current Plan</span>
                  </div>
                )}

                {plan.id === 'pro' && plan.id !== user?.plan && (
                  <div className="text-center mb-6">
                    <span className="px-4 py-2 bg-white/20 backdrop-blur-sm text-white text-xs font-bold rounded-full uppercase tracking-wider shadow-lg">Most Popular</span>
                  </div>
                )}

                <h3 className={`text-3xl font-bold mb-3 ${plan.id === 'pro' ? 'text-white' : 'text-gray-900'}`}>{plan.name}</h3>
                <div className="mb-8 flex items-baseline gap-2">
                  <span className={`text-5xl font-bold ${plan.id === 'pro' ? 'text-white' : 'text-gray-900'}`}>₹{billingCycle === 'yearly' ? plan.price_yearly : plan.price_monthly}</span>
                  <span className={plan.id === 'pro' ? 'text-purple-100' : 'text-gray-500'}>/{billingCycle === 'yearly' ? 'year' : 'month'}</span>
                </div>

                <ul className="space-y-4 mb-10">
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
                  onClick={() => purchasePlan(plan.id)}
                  disabled={loading || plan.id === user?.plan || plan.id === 'free'}
                  className={`w-full py-4 rounded-xl font-semibold transition-all duration-200 shadow-lg ${plan.id === user?.plan
                      ? 'bg-purple-100 text-purple-400 cursor-not-allowed border border-purple-200'
                      : plan.id === 'free'
                        ? 'bg-white text-gray-900 hover:bg-gray-50 border border-gray-200'
                        : plan.id === 'pro'
                          ? 'bg-white text-purple-600 hover:bg-purple-50 hover:scale-105 shadow-white/30'
                          : 'bg-gradient-to-r from-purple-600 to-violet-600 text-white hover:from-purple-700 hover:to-violet-700 hover:scale-105 shadow-purple-300/50'
                    }`}
                >
                  {plan.id === user?.plan ? 'Current Plan' : plan.id === 'free' ? 'Free Plan' : 'Upgrade Now'}
                </button>
              </div>
            ))}
          </div>

          <p className="text-center text-gray-500 mt-12 text-sm">* Payment will be deducted from your wallet balance</p>
        </div>
      </main>
    </div>
  );
};

export default Plans;
