import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { adminAPI } from '../lib/api';
import Sidebar from '../components/Sidebar';
import { CouponModal, PlanModal } from '../components/Modals';

const Admin = () => {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [userSearch, setUserSearch] = useState('');
  const [purchases, setPurchases] = useState([]);
  const [errors, setErrors] = useState([]);
  const [coupons, setCoupons] = useState([]);
  const [plans, setPlans] = useState([]);
  const [aiUsage, setAiUsage] = useState(null);
  const [aiProviders, setAiProviders] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [projects, setProjects] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [settings, setSettings] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showCouponModal, setShowCouponModal] = useState(false);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingCoupon, setEditingCoupon] = useState(null);
  const [editingPlan, setEditingPlan] = useState(null);
  const [loading, setLoading] = useState(false);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'users', label: 'Users', icon: '👥' },
    { id: 'projects', label: 'Projects', icon: '📁' },
    { id: 'billing', label: 'Billing', icon: '💳' },
    { id: 'ai-usage', label: 'AI Usage', icon: '🤖' },
    { id: 'jobs', label: 'Jobs', icon: '⚙️' },
    { id: 'support', label: 'Support', icon: '🎫' },
    { id: 'coupons', label: 'Coupons', icon: '🎟️' },
    { id: 'plans', label: 'Plans', icon: '📋' },
    { id: 'errors', label: 'Errors', icon: '⚠️' },
    { id: 'audit', label: 'Audit', icon: '📜' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ];

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'dashboard') {
        const response = await adminAPI.getStats();
        setStats(response.data);
      } else if (activeTab === 'users') {
        const response = await adminAPI.getUsers(userSearch);
        setUsers(response.data.users);
      } else if (activeTab === 'billing') {
        const response = await adminAPI.getPurchases();
        setPurchases(response.data.purchases);
      } else if (activeTab === 'errors') {
        const response = await adminAPI.getErrors();
        setErrors(response.data.errors);
      } else if (activeTab === 'coupons') {
        const response = await adminAPI.getCoupons();
        setCoupons(response.data.coupons);
      } else if (activeTab === 'plans') {
        const response = await adminAPI.getPlans();
        setPlans(response.data.plans);
      } else if (activeTab === 'ai-usage') {
        const [usageRes, providersRes] = await Promise.all([
          adminAPI.getAIUsage(),
          adminAPI.getAIProviders()
        ]);
        setAiUsage(usageRes.data);
        setAiProviders(providersRes.data.providers);
      } else if (activeTab === 'support') {
        const response = await adminAPI.getSupportTickets();
        setTickets(response.data.tickets);
      } else if (activeTab === 'audit') {
        const response = await adminAPI.getAuditLogs();
        setAuditLogs(response.data.logs);
      } else if (activeTab === 'projects') {
        const response = await adminAPI.getProjects();
        setProjects(response.data.projects);
      } else if (activeTab === 'jobs') {
        const response = await adminAPI.getJobs();
        setJobs(response.data);
      } else if (activeTab === 'settings') {
        const response = await adminAPI.getSettings();
        setSettings(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, userSearch]);

  const handleUserAction = async (userId, action, params = {}) => {
    try {
      if (action === 'ban') await adminAPI.banUser(userId, params.reason);
      else if (action === 'unban') await adminAPI.unbanUser(userId);
      else if (action === 'force-logout') await adminAPI.forceLogout(userId);
      else if (action === 'reset-password') await adminAPI.resetPassword(userId);
      else if (action === 'extend-plan') await adminAPI.extendPlan(userId, params.days);
      else if (action === 'set-limits') await adminAPI.setLimits(userId, params);
      else if (action === 'update') await adminAPI.updateUser(userId, params);
      fetchData();
      alert('Action completed successfully');
    } catch (error) {
      alert(error.response?.data?.detail || 'Action failed');
    }
  };

  const handleRefund = async (purchaseId) => {
    const reason = prompt('Enter refund reason:');
    if (!reason) return;
    try {
      await adminAPI.refundPurchase(purchaseId, reason);
      alert('Refund processed');
      fetchData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Refund failed');
    }
  };

  const handleProviderToggle = async (provider, field, value) => {
    try {
      await adminAPI.updateAIProvider(provider, { [field]: value });
      fetchData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to update provider');
    }
  };

  const handleTicketReply = async (ticketId) => {
    const message = prompt('Enter reply message:');
    if (!message) return;
    try {
      await adminAPI.replyTicket(ticketId, message);
      fetchData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to reply');
    }
  };

  const handleTicketStatus = async (ticketId, status) => {
    try {
      await adminAPI.updateTicketStatus(ticketId, status);
      fetchData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to update status');
    }
  };

  const deleteCoupon = async (couponId) => {
    if (!window.confirm('Are you sure you want to delete this coupon?')) return;
    try {
      await adminAPI.deleteCoupon(couponId);
      fetchData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to delete coupon');
    }
  };

  const deletePlan = async (planId) => {
    if (!window.confirm('Are you sure you want to delete this plan?')) return;
    try {
      await adminAPI.deletePlan(planId);
      fetchData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to delete plan');
    }
  };

  const StatCard = ({ label, value, subtext, color = 'violet' }) => (
    <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
      <p className="text-gray-400 text-sm mb-2">{label}</p>
      <h3 className={`text-3xl font-bold ${color === 'green' ? 'text-green-400' : color === 'red' ? 'text-red-400' : color === 'amber' ? 'text-amber-400' : 'text-white'}`}>{value}</h3>
      {subtext && <p className="text-green-400 text-sm mt-1">{subtext}</p>}
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white flex">
      <Sidebar active="admin" />
      
      <main className="flex-1 p-6 overflow-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Admin Panel</h1>
          {loading && <span className="text-gray-400">Loading...</span>}
        </div>
        
        {/* Tabs */}
        <div className="flex gap-1 mb-6 flex-wrap bg-[#111113] p-1 rounded-xl">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg font-medium transition-all text-sm flex items-center gap-2 ${
                activeTab === tab.id ? 'bg-violet-600 text-white' : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <span>{tab.icon}</span>
              <span className="hidden md:inline">{tab.label}</span>
            </button>
          ))}
        </div>
        
        {/* ========== DASHBOARD TAB ========== */}
        {activeTab === 'dashboard' && stats && (
          <div className="space-y-6">
            {/* Top Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Total Users" value={stats.users?.total || 0} subtext={`+${stats.users?.today_signups || 0} today`} />
              <StatCard label="Pro Users" value={stats.users?.pro || 0} color="violet" />
              <StatCard label="MRR" value={`₹${stats.revenue?.mrr || 0}`} color="green" />
              <StatCard label="Total Revenue" value={`₹${stats.revenue?.total || 0}`} color="green" />
            </div>
            
            {/* Signups & Revenue */}
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
                <h3 className="text-lg font-semibold mb-4">Signups</h3>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div><p className="text-3xl font-bold">{stats.users?.today_signups || 0}</p><p className="text-gray-400 text-sm">Today</p></div>
                  <div><p className="text-3xl font-bold">{stats.users?.week_signups || 0}</p><p className="text-gray-400 text-sm">7 Days</p></div>
                  <div><p className="text-3xl font-bold">{stats.users?.month_signups || 0}</p><p className="text-gray-400 text-sm">30 Days</p></div>
                </div>
              </div>
              <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
                <h3 className="text-lg font-semibold mb-4">Churn</h3>
                <div className="text-center">
                  <p className="text-4xl font-bold text-red-400">{stats.revenue?.churned_30d || 0}</p>
                  <p className="text-gray-400">Cancelled (30d)</p>
                </div>
              </div>
            </div>
            
            {/* Projects & AI Jobs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Projects" value={stats.projects?.total || 0} />
              <StatCard label="Deployments" value={stats.projects?.deployments || 0} />
              <StatCard label="AI Running" value={stats.ai_jobs?.running || 0} color="amber" />
              <StatCard label="AI Failed" value={stats.ai_jobs?.failed || 0} color="red" />
            </div>
            
            {/* AI Usage & Errors */}
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
                <h3 className="text-lg font-semibold mb-4">AI Usage (24h)</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div><p className="text-2xl font-bold">{stats.ai_usage_24h?.total_runs || 0}</p><p className="text-gray-400 text-sm">Total Runs</p></div>
                  <div><p className="text-2xl font-bold text-red-400">{stats.ai_usage_24h?.error_rate || 0}%</p><p className="text-gray-400 text-sm">Error Rate</p></div>
                  <div><p className="text-2xl font-bold text-green-400">${stats.ai_usage_24h?.total_cost || 0}</p><p className="text-gray-400 text-sm">Cost</p></div>
                  <div><p className="text-2xl font-bold">{stats.ai_usage_24h?.failed_runs || 0}</p><p className="text-gray-400 text-sm">Failed</p></div>
                </div>
              </div>
              <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
                <h3 className="text-lg font-semibold mb-4">Errors (24h)</h3>
                <p className="text-4xl font-bold text-red-400 mb-4">{stats.errors_24h?.count || 0}</p>
                <div className="space-y-2">
                  {stats.errors_24h?.top_errors?.slice(0, 3).map((err, i) => (
                    <div key={i} className="flex justify-between text-sm">
                      <span className="text-gray-400">{err.type}</span>
                      <span className="text-red-400">{err.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Plan Distribution & Support */}
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
                <h3 className="text-lg font-semibold mb-4">Plan Distribution</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Free</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div className="h-full bg-gray-500" style={{width: `${(stats.users?.plan_distribution?.free / stats.users?.total * 100) || 0}%`}}></div>
                      </div>
                      <span className="font-bold w-8">{stats.users?.plan_distribution?.free || 0}</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-violet-400">Pro</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div className="h-full bg-violet-500" style={{width: `${(stats.users?.plan_distribution?.pro / stats.users?.total * 100) || 0}%`}}></div>
                      </div>
                      <span className="font-bold w-8">{stats.users?.plan_distribution?.pro || 0}</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-amber-400">Enterprise</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div className="h-full bg-amber-500" style={{width: `${(stats.users?.plan_distribution?.enterprise / stats.users?.total * 100) || 0}%`}}></div>
                      </div>
                      <span className="font-bold w-8">{stats.users?.plan_distribution?.enterprise || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
                <h3 className="text-lg font-semibold mb-4">Support</h3>
                <div className="text-center">
                  <p className="text-4xl font-bold text-amber-400">{stats.support?.open_tickets || 0}</p>
                  <p className="text-gray-400">Open Tickets</p>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* ========== USERS TAB ========== */}
        {activeTab === 'users' && (
          <div className="space-y-4">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="Search by email, name, or ID..."
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                className="flex-1 px-4 py-3 bg-[#111113] border border-white/10 rounded-xl focus:outline-none focus:border-violet-500"
              />
            </div>
            
            <div className="bg-[#111113] border border-white/5 rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-[#0a0a0b]">
                  <tr>
                    <th className="px-4 py-3 text-left text-gray-400 font-medium">User</th>
                    <th className="px-4 py-3 text-left text-gray-400 font-medium">Plan</th>
                    <th className="px-4 py-3 text-left text-gray-400 font-medium">Projects</th>
                    <th className="px-4 py-3 text-left text-gray-400 font-medium">Revenue</th>
                    <th className="px-4 py-3 text-left text-gray-400 font-medium">Status</th>
                    <th className="px-4 py-3 text-left text-gray-400 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u, i) => (
                    <tr key={u.id || i} className="border-t border-white/5 hover:bg-white/5">
                      <td className="px-4 py-3">
                        <p className="font-medium">{u.name}</p>
                        <p className="text-xs text-gray-500">{u.email}</p>
                        <p className="text-xs text-gray-600">{u.created_at?.split('T')[0]}</p>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          u.plan === 'enterprise' ? 'bg-amber-500/20 text-amber-400' :
                          u.plan === 'pro' ? 'bg-violet-500/20 text-violet-400' :
                          'bg-gray-500/20 text-gray-400'
                        }`}>{u.plan?.toUpperCase()}</span>
                        {u.plan_expiry && <p className="text-xs text-gray-500 mt-1">Exp: {u.plan_expiry?.split('T')[0]}</p>}
                      </td>
                      <td className="px-4 py-3">
                        <p>{u.projects_count || 0} projects</p>
                        <p className="text-xs text-gray-500">{u.deployments_count || 0} deploys</p>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-green-400">₹{u.total_revenue || 0}</p>
                        <p className="text-xs text-gray-500">Wallet: ₹{u.wallet_balance?.toFixed(0) || 0}</p>
                      </td>
                      <td className="px-4 py-3">
                        {u.is_banned ? (
                          <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded-full text-xs">Banned</span>
                        ) : u.is_admin ? (
                          <span className="px-2 py-1 bg-violet-500/20 text-violet-400 rounded-full text-xs">Admin</span>
                        ) : (
                          <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded-full text-xs">Active</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {u.is_banned ? (
                            <button onClick={() => handleUserAction(u.id, 'unban')} className="px-2 py-1 bg-green-600/20 text-green-400 rounded text-xs">Unban</button>
                          ) : (
                            <button onClick={() => handleUserAction(u.id, 'ban', { reason: prompt('Ban reason:') })} className="px-2 py-1 bg-red-600/20 text-red-400 rounded text-xs">Ban</button>
                          )}
                          <button onClick={() => handleUserAction(u.id, 'force-logout')} className="px-2 py-1 bg-orange-600/20 text-orange-400 rounded text-xs">Logout</button>
                          <button onClick={() => handleUserAction(u.id, 'extend-plan', { days: parseInt(prompt('Days to extend:', '7')) || 7 })} className="px-2 py-1 bg-blue-600/20 text-blue-400 rounded text-xs">+7d</button>
                          <button onClick={() => {
                            const plan = prompt('New plan (free/pro/enterprise):');
                            if (plan) handleUserAction(u.id, 'update', { plan });
                          }} className="px-2 py-1 bg-violet-600/20 text-violet-400 rounded text-xs">Plan</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {/* ========== BILLING TAB ========== */}
        {activeTab === 'billing' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Purchases & Payments</h2>
              <button onClick={async () => {
                const res = await adminAPI.exportInvoices();
                const blob = new Blob([res.data.csv_data], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'invoices.csv';
                a.click();
              }} className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg text-sm">
                Export CSV
              </button>
            </div>
            
            <div className="bg-[#111113] border border-white/5 rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-[#0a0a0b]">
                  <tr>
                    <th className="px-4 py-3 text-left text-gray-400">User</th>
                    <th className="px-4 py-3 text-left text-gray-400">Plan</th>
                    <th className="px-4 py-3 text-left text-gray-400">Amount</th>
                    <th className="px-4 py-3 text-left text-gray-400">Coupon</th>
                    <th className="px-4 py-3 text-left text-gray-400">Status</th>
                    <th className="px-4 py-3 text-left text-gray-400">Date</th>
                    <th className="px-4 py-3 text-left text-gray-400">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {purchases.map((p, i) => (
                    <tr key={p.id || i} className="border-t border-white/5">
                      <td className="px-4 py-3">
                        <p className="font-medium">{p.user_name}</p>
                        <p className="text-xs text-gray-500">{p.user_email}</p>
                      </td>
                      <td className="px-4 py-3">{p.plan?.toUpperCase()} ({p.billing_cycle})</td>
                      <td className="px-4 py-3">
                        <p>₹{p.amount}</p>
                        {p.coupon_discount > 0 && <p className="text-green-400 text-xs">-₹{p.coupon_discount}</p>}
                      </td>
                      <td className="px-4 py-3">{p.coupon_code || '-'}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          p.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                          p.status === 'refunded' ? 'bg-red-500/20 text-red-400' :
                          'bg-yellow-500/20 text-yellow-400'
                        }`}>{p.status}</span>
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{new Date(p.created_at).toLocaleString()}</td>
                      <td className="px-4 py-3">
                        {p.status === 'completed' && (
                          <button onClick={() => handleRefund(p.id)} className="px-2 py-1 bg-red-600/20 text-red-400 rounded text-xs">Refund</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {/* ========== AI USAGE TAB ========== */}
        {activeTab === 'ai-usage' && aiUsage && (
          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Total Runs" value={aiUsage.stats?.success_count + aiUsage.stats?.fail_count || 0} />
              <StatCard label="Success" value={aiUsage.stats?.success_count || 0} color="green" />
              <StatCard label="Failed" value={aiUsage.stats?.fail_count || 0} color="red" />
              <StatCard label="BYO Keys" value={aiUsage.stats?.byo_key_count || 0} color="amber" />
            </div>
            
            <div className="grid md:grid-cols-2 gap-4">
              <StatCard label="Total Cost" value={`$${aiUsage.stats?.total_cost || 0}`} color="green" />
              <StatCard label="Total Tokens" value={(aiUsage.stats?.total_tokens || 0).toLocaleString()} />
            </div>
            
            {/* Provider Controls */}
            <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
              <h3 className="text-lg font-semibold mb-4">AI Provider Controls</h3>
              <div className="space-y-4">
                {aiProviders.map((prov, i) => (
                  <div key={prov.provider || i} className="flex items-center justify-between p-4 bg-[#0a0a0b] rounded-xl">
                    <div>
                      <p className="font-medium capitalize">{prov.provider}</p>
                      <p className={`text-sm ${prov.health_status === 'healthy' ? 'text-green-400' : prov.health_status === 'slow' ? 'text-yellow-400' : 'text-red-400'}`}>
                        Status: {prov.health_status}
                      </p>
                    </div>
                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={prov.is_enabled} onChange={(e) => handleProviderToggle(prov.provider, 'is_enabled', e.target.checked)} className="w-4 h-4" />
                        <span className="text-sm">Enabled</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={prov.is_default} onChange={(e) => handleProviderToggle(prov.provider, 'is_default', e.target.checked)} className="w-4 h-4" />
                        <span className="text-sm">Default</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={prov.is_blocked} onChange={(e) => handleProviderToggle(prov.provider, 'is_blocked', e.target.checked)} className="w-4 h-4" />
                        <span className="text-sm text-red-400">Blocked</span>
                      </label>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Usage by Provider */}
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
                <h3 className="text-lg font-semibold mb-4">By Provider</h3>
                <div className="space-y-3">
                  {Object.entries(aiUsage.stats?.by_provider || {}).map(([prov, count]) => (
                    <div key={prov} className="flex justify-between">
                      <span className="text-gray-400 capitalize">{prov}</span>
                      <span className="font-bold">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
                <h3 className="text-lg font-semibold mb-4">By Model</h3>
                <div className="space-y-3">
                  {Object.entries(aiUsage.stats?.by_model || {}).map(([model, count]) => (
                    <div key={model} className="flex justify-between">
                      <span className="text-gray-400 text-sm">{model}</span>
                      <span className="font-bold">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Recent Runs */}
            <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
              <h3 className="text-lg font-semibold mb-4">Recent AI Runs</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-400">
                      <th className="pb-3">Provider</th>
                      <th className="pb-3">Model</th>
                      <th className="pb-3">Tokens</th>
                      <th className="pb-3">Cost</th>
                      <th className="pb-3">Latency</th>
                      <th className="pb-3">Status</th>
                      <th className="pb-3">BYO</th>
                    </tr>
                  </thead>
                  <tbody>
                    {aiUsage.runs?.slice(0, 20).map((run, i) => (
                      <tr key={run.id || i} className="border-t border-white/5">
                        <td className="py-2 capitalize">{run.provider}</td>
                        <td className="py-2 text-gray-400 text-xs">{run.model}</td>
                        <td className="py-2">{run.tokens_in + run.tokens_out}</td>
                        <td className="py-2 text-green-400">${run.cost_estimate}</td>
                        <td className="py-2">{run.latency_ms}ms</td>
                        <td className="py-2">
                          <span className={run.status === 'success' ? 'text-green-400' : 'text-red-400'}>{run.status}</span>
                        </td>
                        <td className="py-2">{run.is_byo_key ? '✓' : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
        
        {/* ========== SUPPORT TAB ========== */}
        {activeTab === 'support' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Support Tickets (Priority Queue)</h2>
            
            {tickets.length === 0 ? (
              <div className="bg-[#111113] border border-white/5 rounded-2xl p-8 text-center">
                <p className="text-gray-500">No tickets 🎉</p>
              </div>
            ) : (
              <div className="space-y-4">
                {tickets.map((ticket, i) => (
                  <div key={ticket.id || i} className={`bg-[#111113] border rounded-2xl p-6 ${
                    ticket.priority >= 100 ? 'border-amber-500/30' :
                    ticket.priority >= 50 ? 'border-violet-500/30' :
                    'border-white/5'
                  }`}>
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            ticket.status === 'open' ? 'bg-red-500/20 text-red-400' :
                            ticket.status === 'in_progress' ? 'bg-yellow-500/20 text-yellow-400' :
                            ticket.status === 'resolved' ? 'bg-green-500/20 text-green-400' :
                            'bg-gray-500/20 text-gray-400'
                          }`}>{ticket.status}</span>
                          <span className={`px-2 py-1 rounded text-xs ${
                            ticket.user_plan === 'enterprise' ? 'bg-amber-500/20 text-amber-400' :
                            ticket.user_plan === 'pro' ? 'bg-violet-500/20 text-violet-400' :
                            'bg-gray-500/20 text-gray-400'
                          }`}>{ticket.user_plan}</span>
                          <span className="text-gray-500 text-xs">Priority: {ticket.priority}</span>
                        </div>
                        <h3 className="font-semibold text-lg">{ticket.subject}</h3>
                        <p className="text-gray-400 text-sm">{ticket.user_name} ({ticket.user_email})</p>
                        <p className="text-gray-500 text-xs">Revenue: ₹{ticket.user_revenue}</p>
                      </div>
                      <span className="text-gray-500 text-sm">{new Date(ticket.created_at).toLocaleString()}</span>
                    </div>
                    
                    <p className="text-gray-300 mb-4">{ticket.description}</p>
                    
                    {ticket.messages?.length > 1 && (
                      <div className="mb-4 max-h-40 overflow-y-auto space-y-2">
                        {ticket.messages.slice(1).map((msg, mi) => (
                          <div key={mi} className={`p-3 rounded-lg text-sm ${msg.sender === 'admin' ? 'bg-violet-500/10 ml-8' : 'bg-white/5 mr-8'}`}>
                            <p className="text-gray-400 text-xs mb-1">{msg.sender === 'admin' ? msg.sender_name || 'Admin' : 'User'}</p>
                            <p>{msg.message}</p>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    <div className="flex gap-2">
                      <button onClick={() => handleTicketReply(ticket.id)} className="px-4 py-2 bg-violet-600/20 text-violet-400 rounded-lg text-sm">Reply</button>
                      <button onClick={() => handleTicketStatus(ticket.id, 'in_progress')} className="px-4 py-2 bg-yellow-600/20 text-yellow-400 rounded-lg text-sm">In Progress</button>
                      <button onClick={() => handleTicketStatus(ticket.id, 'resolved')} className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg text-sm">Resolve</button>
                      <button onClick={() => handleTicketStatus(ticket.id, 'closed')} className="px-4 py-2 bg-gray-600/20 text-gray-400 rounded-lg text-sm">Close</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* ========== COUPONS TAB ========== */}
        {activeTab === 'coupons' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Coupons & Offers</h2>
              <button onClick={() => { setEditingCoupon(null); setShowCouponModal(true); }} className="px-4 py-2 bg-violet-600 rounded-lg font-medium hover:bg-violet-700">
                + Create Coupon
              </button>
            </div>
            
            {coupons.length === 0 ? (
              <div className="bg-[#111113] border border-white/5 rounded-2xl p-8 text-center">
                <p className="text-gray-500">No coupons created yet</p>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {coupons.map((c, i) => (
                  <div key={c.id || i} className={`bg-[#111113] border rounded-2xl p-6 ${c.is_active ? 'border-green-500/30' : 'border-white/5 opacity-60'}`}>
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-xl font-bold text-violet-400">{c.code}</h3>
                        <p className="text-sm text-gray-400">
                          {c.discount_type === 'percentage' ? `${c.discount_value}% OFF` : `₹${c.discount_value} OFF`}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs ${c.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                        {c.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <div className="space-y-1 text-sm text-gray-400 mb-4">
                      <p>Used: {c.used_count} / {c.usage_limit === -1 ? '∞' : c.usage_limit}</p>
                      {c.valid_until && <p>Expires: {new Date(c.valid_until).toLocaleDateString()}</p>}
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => { setEditingCoupon(c); setShowCouponModal(true); }} className="flex-1 px-3 py-2 bg-violet-600/20 text-violet-400 rounded-lg text-sm">Edit</button>
                      <button onClick={() => deleteCoupon(c.id)} className="px-3 py-2 bg-red-500/20 text-red-400 rounded-lg text-sm">Delete</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* ========== PLANS TAB ========== */}
        {activeTab === 'plans' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Plans Management</h2>
              <button onClick={() => { setEditingPlan(null); setShowPlanModal(true); }} className="px-4 py-2 bg-violet-600 rounded-lg font-medium hover:bg-violet-700">
                + Create Plan
              </button>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {plans.map((plan, i) => (
                <div key={plan.id || i} className="bg-[#111113] border border-white/10 rounded-2xl p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-xl font-bold">{plan.name}</h3>
                    {plan.from_default && <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded-full text-xs">Default</span>}
                  </div>
                  <p className="text-2xl font-bold text-violet-400 mb-4">₹{plan.price_monthly}<span className="text-sm text-gray-400">/mo</span></p>
                  <div className="space-y-1 text-sm text-gray-400 mb-4">
                    <p>Projects: {plan.limits?.projects === -1 ? '∞' : plan.limits?.projects}</p>
                    <p>Generations: {plan.limits?.generations_per_month === -1 ? '∞' : plan.limits?.generations_per_month}/mo</p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => { setEditingPlan(plan); setShowPlanModal(true); }} className="flex-1 px-3 py-2 bg-violet-600/20 text-violet-400 rounded-lg text-sm">Edit</button>
                    {plan.id !== 'free' && !plan.from_default && (
                      <button onClick={() => deletePlan(plan.id)} className="px-3 py-2 bg-red-500/20 text-red-400 rounded-lg text-sm">Delete</button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* ========== ERRORS TAB ========== */}
        {activeTab === 'errors' && (
          <div className="space-y-4">
            {errors.length === 0 ? (
              <div className="bg-[#111113] border border-white/5 rounded-2xl p-8 text-center">
                <p className="text-gray-500">No errors logged 🎉</p>
              </div>
            ) : (
              errors.map((err, i) => (
                <div key={err.id || i} className="bg-[#111113] border border-red-500/20 rounded-2xl p-6">
                  <div className="flex justify-between items-start mb-2">
                    <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-sm font-medium">{err.error_type}</span>
                    <span className="text-gray-500 text-sm">{new Date(err.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-gray-400 text-sm mb-2">{err.endpoint}</p>
                  <p className="text-red-400">{err.error_message}</p>
                </div>
              ))
            )}
          </div>
        )}
        
        {/* ========== PROJECTS TAB ========== */}
        {activeTab === 'projects' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Projects Management</h2>
            
            <div className="bg-[#111113] border border-white/5 rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-[#0a0a0b]">
                  <tr>
                    <th className="px-4 py-3 text-left text-gray-400">Project</th>
                    <th className="px-4 py-3 text-left text-gray-400">Owner</th>
                    <th className="px-4 py-3 text-left text-gray-400">Status</th>
                    <th className="px-4 py-3 text-left text-gray-400">Created</th>
                    <th className="px-4 py-3 text-left text-gray-400">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p, i) => (
                    <tr key={p.id || i} className="border-t border-white/5">
                      <td className="px-4 py-3">
                        <p className="font-medium">{p.name}</p>
                        <p className="text-xs text-gray-500">{p.id?.slice(0, 8)}...</p>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-sm">{p.owner?.name}</p>
                        <p className="text-xs text-gray-500">{p.owner?.email}</p>
                      </td>
                      <td className="px-4 py-3">
                        {p.is_frozen ? (
                          <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded-full text-xs">Frozen</span>
                        ) : (
                          <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded-full text-xs">Active</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{new Date(p.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          {p.is_frozen ? (
                            <button onClick={() => adminAPI.unfreezeProject(p.id).then(fetchData)} className="px-2 py-1 bg-green-600/20 text-green-400 rounded text-xs">Unfreeze</button>
                          ) : (
                            <button onClick={() => adminAPI.freezeProject(p.id, prompt('Freeze reason:')).then(fetchData)} className="px-2 py-1 bg-yellow-600/20 text-yellow-400 rounded text-xs">Freeze</button>
                          )}
                          <button onClick={() => adminAPI.regenerateProject(p.id).then(() => alert('Regeneration queued'))} className="px-2 py-1 bg-violet-600/20 text-violet-400 rounded text-xs">Regen</button>
                          <button onClick={() => { if(window.confirm('Delete project?')) adminAPI.deleteProject(p.id).then(fetchData) }} className="px-2 py-1 bg-red-600/20 text-red-400 rounded text-xs">Delete</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {/* ========== JOBS TAB ========== */}
        {activeTab === 'jobs' && jobs && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Jobs & Build Logs</h2>
            
            {/* Job Stats */}
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-[#111113] border border-white/5 rounded-xl p-4 text-center">
                <p className="text-2xl font-bold text-yellow-400">{jobs.counts?.queued || 0}</p>
                <p className="text-gray-400 text-sm">Queued</p>
              </div>
              <div className="bg-[#111113] border border-white/5 rounded-xl p-4 text-center">
                <p className="text-2xl font-bold text-blue-400">{jobs.counts?.running || 0}</p>
                <p className="text-gray-400 text-sm">Running</p>
              </div>
              <div className="bg-[#111113] border border-white/5 rounded-xl p-4 text-center">
                <p className="text-2xl font-bold text-green-400">{jobs.counts?.completed || 0}</p>
                <p className="text-gray-400 text-sm">Completed</p>
              </div>
              <div className="bg-[#111113] border border-white/5 rounded-xl p-4 text-center">
                <p className="text-2xl font-bold text-red-400">{jobs.counts?.failed || 0}</p>
                <p className="text-gray-400 text-sm">Failed</p>
              </div>
            </div>
            
            {/* Jobs List */}
            <div className="bg-[#111113] border border-white/5 rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-[#0a0a0b]">
                  <tr>
                    <th className="px-4 py-3 text-left text-gray-400">Job</th>
                    <th className="px-4 py-3 text-left text-gray-400">User</th>
                    <th className="px-4 py-3 text-left text-gray-400">Project</th>
                    <th className="px-4 py-3 text-left text-gray-400">Status</th>
                    <th className="px-4 py-3 text-left text-gray-400">Created</th>
                    <th className="px-4 py-3 text-left text-gray-400">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(jobs.jobs || []).map((job, i) => (
                    <tr key={job.id || i} className="border-t border-white/5">
                      <td className="px-4 py-3">
                        <p className="font-medium">{job.job_type}</p>
                        <p className="text-xs text-gray-500">{job.id?.slice(0, 8)}...</p>
                      </td>
                      <td className="px-4 py-3 text-gray-300">{job.user?.name || 'Unknown'}</td>
                      <td className="px-4 py-3 text-gray-400">{job.project?.name || 'N/A'}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          job.status === 'queued' ? 'bg-yellow-500/20 text-yellow-400' :
                          job.status === 'running' ? 'bg-blue-500/20 text-blue-400' :
                          job.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>{job.status}</span>
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{new Date(job.created_at).toLocaleString()}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          {job.status === 'failed' && (
                            <button onClick={() => adminAPI.retryJob(job.id).then(() => { alert('Job queued for retry'); fetchData(); })} className="px-2 py-1 bg-blue-600/20 text-blue-400 rounded text-xs">Retry</button>
                          )}
                          {!job.resolved && (
                            <button onClick={() => adminAPI.resolveJob(job.id, prompt('Resolution notes:')).then(fetchData)} className="px-2 py-1 bg-green-600/20 text-green-400 rounded text-xs">Resolve</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {/* ========== SETTINGS TAB ========== */}
        {activeTab === 'settings' && settings && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold">Platform Settings</h2>
            
            {/* Maintenance Mode */}
            <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-semibold">Maintenance Mode</h3>
                  <p className="text-gray-400 text-sm">Enable to show maintenance page to users</p>
                </div>
                <button
                  onClick={async () => {
                    const msg = settings.maintenance_mode ? '' : prompt('Maintenance message:');
                    await adminAPI.toggleMaintenance(!settings.maintenance_mode, msg);
                    fetchData();
                  }}
                  className={`px-4 py-2 rounded-lg font-medium ${settings.maintenance_mode ? 'bg-green-600' : 'bg-red-600'}`}
                >
                  {settings.maintenance_mode ? 'Disable' : 'Enable'}
                </button>
              </div>
              {settings.maintenance_mode && settings.maintenance_message && (
                <p className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-yellow-400">
                  {settings.maintenance_message}
                </p>
              )}
            </div>
            
            {/* Feature Flags */}
            <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
              <h3 className="text-lg font-semibold mb-4">Feature Flags</h3>
              <div className="space-y-4">
                {Object.entries(settings.feature_flags || {}).map(([flag, enabled]) => (
                  <div key={flag} className="flex justify-between items-center p-3 bg-[#0a0a0b] rounded-lg">
                    <span className="text-gray-300 capitalize">{flag.replace(/_/g, ' ')}</span>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={enabled}
                        onChange={async (e) => {
                          const newFlags = { ...settings.feature_flags, [flag]: e.target.checked };
                          await adminAPI.updateFeatureFlags(newFlags);
                          fetchData();
                        }}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-violet-600"></div>
                    </label>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Rate Limits */}
            <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
              <h3 className="text-lg font-semibold mb-4">Rate Limits</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="text-gray-400 text-sm">Requests per minute</label>
                  <input
                    type="number"
                    value={settings.rate_limits?.requests_per_minute || 60}
                    readOnly
                    className="w-full mt-1 px-4 py-2 bg-[#0a0a0b] border border-white/10 rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-gray-400 text-sm">Generations per hour</label>
                  <input
                    type="number"
                    value={settings.rate_limits?.generations_per_hour || 20}
                    readOnly
                    className="w-full mt-1 px-4 py-2 bg-[#0a0a0b] border border-white/10 rounded-lg"
                  />
                </div>
              </div>
            </div>
            
            {/* Default AI Provider */}
            <div className="bg-[#111113] border border-white/5 rounded-2xl p-6">
              <h3 className="text-lg font-semibold mb-4">Default AI Provider</h3>
              <p className="text-violet-400 text-lg font-medium capitalize">{settings.default_ai_provider || 'openai'}</p>
            </div>
          </div>
        )}
        
        {/* ========== AUDIT TAB ========== */}
        {activeTab === 'audit' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Admin Audit Log</h2>
            
            {auditLogs.length === 0 ? (
              <div className="bg-[#111113] border border-white/5 rounded-2xl p-8 text-center">
                <p className="text-gray-500">No audit logs yet</p>
              </div>
            ) : (
              <div className="bg-[#111113] border border-white/5 rounded-2xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-[#0a0a0b]">
                    <tr>
                      <th className="px-4 py-3 text-left text-gray-400">Admin</th>
                      <th className="px-4 py-3 text-left text-gray-400">Action</th>
                      <th className="px-4 py-3 text-left text-gray-400">Target</th>
                      <th className="px-4 py-3 text-left text-gray-400">Reason</th>
                      <th className="px-4 py-3 text-left text-gray-400">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map((log, i) => (
                      <tr key={log.id || i} className="border-t border-white/5">
                        <td className="px-4 py-3 text-gray-300">{log.admin_email}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-1 bg-violet-500/20 text-violet-400 rounded text-xs">{log.action}</span>
                        </td>
                        <td className="px-4 py-3 text-gray-400">{log.target_type}: {log.target_id?.slice(0, 8)}...</td>
                        <td className="px-4 py-3 text-gray-500">{log.reason || '-'}</td>
                        <td className="px-4 py-3 text-gray-500 text-xs">{new Date(log.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
      
      {/* Modals */}
      {showCouponModal && (
        <CouponModal coupon={editingCoupon} onClose={() => setShowCouponModal(false)} onSave={() => { setShowCouponModal(false); fetchData(); }} token={token} />
      )}
      {showPlanModal && (
        <PlanModal plan={editingPlan} onClose={() => setShowPlanModal(false)} onSave={() => { setShowPlanModal(false); fetchData(); }} token={token} />
      )}
    </div>
  );
};

export default Admin;
