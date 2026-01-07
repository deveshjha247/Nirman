import React, { useState } from 'react';
import { adminAPI } from '../lib/api';

// Coupon Modal Component
export const CouponModal = ({ coupon, onClose, onSave, token }) => {
  const [form, setForm] = useState({
    code: coupon?.code || '',
    discount_type: coupon?.discount_type || 'percentage',
    discount_value: coupon?.discount_value || 10,
    min_purchase: coupon?.min_purchase || 0,
    max_discount: coupon?.max_discount || '',
    valid_until: coupon?.valid_until ? coupon.valid_until.split('T')[0] : '',
    usage_limit: coupon?.usage_limit || -1,
    applicable_plans: coupon?.applicable_plans?.join(', ') || '',
    is_active: coupon?.is_active !== false
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = {
        ...form,
        max_discount: form.max_discount ? parseFloat(form.max_discount) : null,
        valid_until: form.valid_until || null,
        applicable_plans: form.applicable_plans ? form.applicable_plans.split(',').map(p => p.trim()).filter(Boolean) : []
      };
      
      if (coupon) {
        await adminAPI.updateCoupon(coupon.id, data);
      } else {
        await adminAPI.createCoupon(data);
      }
      onSave();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to save coupon');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-6">
      <div className="bg-[#111113] border border-white/10 rounded-2xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4 text-white">{coupon ? 'Edit Coupon' : 'Create Coupon'}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Coupon Code</label>
            <input type="text" value={form.code} onChange={(e) => setForm({...form, code: e.target.value.toUpperCase()})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" placeholder="SAVE20" required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Discount Type</label>
              <select value={form.discount_type} onChange={(e) => setForm({...form, discount_type: e.target.value})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white">
                <option value="percentage">Percentage (%)</option>
                <option value="fixed">Fixed Amount (₹)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Discount Value</label>
              <input type="number" value={form.discount_value} onChange={(e) => setForm({...form, discount_value: parseFloat(e.target.value)})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" required />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Min Purchase (₹)</label>
              <input type="number" value={form.min_purchase} onChange={(e) => setForm({...form, min_purchase: parseFloat(e.target.value)})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Max Discount (₹)</label>
              <input type="number" value={form.max_discount} onChange={(e) => setForm({...form, max_discount: e.target.value})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" placeholder="Optional" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Valid Until</label>
              <input type="date" value={form.valid_until} onChange={(e) => setForm({...form, valid_until: e.target.value})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Usage Limit</label>
              <input type="number" value={form.usage_limit} onChange={(e) => setForm({...form, usage_limit: parseInt(e.target.value)})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" placeholder="-1 for unlimited" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Applicable Plans (comma separated)</label>
            <input type="text" value={form.applicable_plans} onChange={(e) => setForm({...form, applicable_plans: e.target.value})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" placeholder="pro, enterprise (empty = all)" />
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({...form, is_active: e.target.checked})} className="w-4 h-4" />
            <label className="text-gray-300">Active</label>
          </div>
          <div className="flex gap-3">
            <button type="button" onClick={onClose} className="flex-1 py-3 bg-white/5 border border-white/10 rounded-xl font-medium text-white hover:bg-white/10">Cancel</button>
            <button type="submit" disabled={loading} className="flex-1 py-3 bg-violet-600 rounded-xl font-semibold text-white hover:bg-violet-700 disabled:opacity-50">{loading ? 'Saving...' : 'Save'}</button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Plan Modal Component
export const PlanModal = ({ plan, onClose, onSave, token }) => {
  const [form, setForm] = useState({
    id: plan?.id || '',
    name: plan?.name || '',
    price_monthly: plan?.price_monthly || 0,
    price_yearly: plan?.price_yearly || 0,
    features: plan?.features?.join('\n') || '',
    projects_limit: plan?.limits?.projects || 5,
    generations_limit: plan?.limits?.generations_per_month || 100,
    is_active: plan?.is_active !== false,
    sort_order: plan?.sort_order || 0
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = {
        id: form.id,
        name: form.name,
        price_monthly: form.price_monthly,
        price_yearly: form.price_yearly,
        features: form.features.split('\n').filter(f => f.trim()),
        limits: {
          projects: form.projects_limit,
          generations_per_month: form.generations_limit
        },
        is_active: form.is_active,
        sort_order: form.sort_order
      };
      
      if (plan) {
        await adminAPI.updatePlan(plan.id, data);
      } else {
        await adminAPI.createPlan(data);
      }
      onSave();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to save plan');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-6">
      <div className="bg-[#111113] border border-white/10 rounded-2xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4 text-white">{plan ? 'Edit Plan' : 'Create Plan'}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Plan ID</label>
              <input type="text" value={form.id} onChange={(e) => setForm({...form, id: e.target.value.toLowerCase()})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" placeholder="pro" required disabled={!!plan} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Plan Name</label>
              <input type="text" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" placeholder="Pro Plan" required />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Monthly Price (₹)</label>
              <input type="number" value={form.price_monthly} onChange={(e) => setForm({...form, price_monthly: parseFloat(e.target.value)})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Yearly Price (₹)</label>
              <input type="number" value={form.price_yearly} onChange={(e) => setForm({...form, price_yearly: parseFloat(e.target.value)})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" required />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Projects Limit</label>
              <input type="number" value={form.projects_limit} onChange={(e) => setForm({...form, projects_limit: parseInt(e.target.value)})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" placeholder="-1 for unlimited" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Generations/Month</label>
              <input type="number" value={form.generations_limit} onChange={(e) => setForm({...form, generations_limit: parseInt(e.target.value)})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" placeholder="-1 for unlimited" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Features (one per line)</label>
            <textarea value={form.features} onChange={(e) => setForm({...form, features: e.target.value})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white resize-none" rows={5} placeholder="Unlimited Projects&#10;Priority Support&#10;Custom Domains" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Sort Order</label>
              <input type="number" value={form.sort_order} onChange={(e) => setForm({...form, sort_order: parseInt(e.target.value)})} className="w-full px-4 py-3 bg-[#0a0a0b] border border-white/10 rounded-xl text-white" />
            </div>
            <div className="flex items-center gap-2 pt-8">
              <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({...form, is_active: e.target.checked})} className="w-4 h-4" />
              <label className="text-gray-300">Active</label>
            </div>
          </div>
          <div className="flex gap-3">
            <button type="button" onClick={onClose} className="flex-1 py-3 bg-white/5 border border-white/10 rounded-xl font-medium text-white hover:bg-white/10">Cancel</button>
            <button type="submit" disabled={loading} className="flex-1 py-3 bg-violet-600 rounded-xl font-semibold text-white hover:bg-violet-700 disabled:opacity-50">{loading ? 'Saving...' : 'Save'}</button>
          </div>
        </form>
      </div>
    </div>
  );
};
