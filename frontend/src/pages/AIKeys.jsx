import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { aiKeysAPI } from '../lib/api';
import Sidebar from '../components/Sidebar';

const AIKeys = () => {
  const { user } = useAuth();
  const [providers, setProviders] = useState([]);
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [addingKey, setAddingKey] = useState(null);
  const [newKey, setNewKey] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [providersRes, usageRes] = await Promise.all([
        aiKeysAPI.getProviders(),
        aiKeysAPI.getUsage()
      ]);
      setProviders(providersRes.data.providers);
      setUsage(usageRes.data);
    } catch (error) {
      console.error('Failed to fetch AI keys data:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAddKey = async (provider) => {
    if (!newKey.trim()) {
      alert('Please enter an API key');
      return;
    }
    
    try {
      await aiKeysAPI.addKey(provider, newKey);
      setAddingKey(null);
      setNewKey('');
      fetchData();
      alert('API key added successfully!');
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to add key');
    }
  };

  const handleDeleteKey = async (provider) => {
    if (!window.confirm(`Are you sure you want to delete your ${provider} API key?`)) return;
    
    try {
      await aiKeysAPI.deleteKey(provider);
      fetchData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to delete key');
    }
  };

  const handleToggleKey = async (provider, currentStatus) => {
    try {
      await aiKeysAPI.toggleKey(provider, !currentStatus);
      fetchData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to toggle key');
    }
  };

  const providerIcons = {
    // US/Global Providers
    openai: '🤖',
    gemini: '✨',
    claude: '🧠',
    grok: '🚀',
    mistral: '🌀',
    cohere: '💎',
    groq: '⚡',
    together: '🤝',
    perplexity: '🔍',
    fireworks: '🎆',
    ai21: '🔬',
    // Chinese AI Providers
    deepseek: '🌊',
    qwen: '🐼',
    moonshot: '🌙',
    yi: '🎯',
    zhipu: '🔮',
    // Open Source
    huggingface: '🤗'
  };

  const providerColors = {
    // US/Global Providers
    openai: 'from-green-50 to-emerald-50 border-green-200',
    gemini: 'from-blue-50 to-sky-50 border-blue-200',
    claude: 'from-orange-50 to-amber-50 border-orange-200',
    grok: 'from-purple-50 to-violet-50 border-purple-200',
    mistral: 'from-indigo-50 to-blue-50 border-indigo-200',
    cohere: 'from-pink-50 to-rose-50 border-pink-200',
    groq: 'from-yellow-50 to-amber-50 border-yellow-200',
    together: 'from-teal-50 to-emerald-50 border-teal-200',
    perplexity: 'from-sky-50 to-cyan-50 border-sky-200',
    fireworks: 'from-red-50 to-orange-50 border-red-200',
    ai21: 'from-slate-50 to-gray-50 border-slate-200',
    // Chinese AI Providers
    deepseek: 'from-cyan-50 to-teal-50 border-cyan-200',
    qwen: 'from-orange-50 to-red-50 border-orange-200',
    moonshot: 'from-violet-50 to-purple-50 border-violet-200',
    yi: 'from-lime-50 to-green-50 border-lime-200',
    zhipu: 'from-fuchsia-50 to-pink-50 border-fuchsia-200',
    // Open Source
    huggingface: 'from-amber-50 to-yellow-50 border-amber-200'
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50/30 via-white to-purple-50/30 flex">
      <Sidebar active="ai-keys" />
      
      <main className="flex-1 p-8 overflow-auto">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center gap-3">
              <span className="text-5xl">🔑</span>
              AI API Keys
            </h1>
            <p className="text-gray-600 text-lg leading-relaxed">
              Bring your own API keys (BYO-AI) to use your preferred AI provider. 
              Your keys are encrypted and never exposed.
            </p>
          </div>

          {/* Usage Stats */}
          {usage && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
              <div className="bg-white/90 backdrop-blur-sm border border-purple-100 rounded-2xl p-6 shadow-xl shadow-purple-100/20 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300">
                <p className="text-gray-500 text-sm font-medium mb-2">Total Runs</p>
                <p className="text-3xl font-bold text-gray-900">{usage.total_runs}</p>
              </div>
              <div className="bg-white/90 backdrop-blur-sm border border-green-200 rounded-2xl p-6 shadow-xl shadow-green-100/20 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300">
                <p className="text-gray-500 text-sm font-medium mb-2">BYO Key Runs</p>
                <p className="text-3xl font-bold text-green-600">{usage.byo_runs}</p>
              </div>
              <div className="bg-white/90 backdrop-blur-sm border border-purple-200 rounded-2xl p-6 shadow-xl shadow-purple-100/20 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300">
                <p className="text-gray-500 text-sm font-medium mb-2">Platform Runs</p>
                <p className="text-3xl font-bold text-purple-600">{usage.platform_runs}</p>
              </div>
              <div className="bg-white/90 backdrop-blur-sm border border-amber-200 rounded-2xl p-6 shadow-xl shadow-amber-100/20 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300">
                <p className="text-gray-500 text-sm font-medium mb-2">Est. Cost Saved</p>
                <p className="text-3xl font-bold text-amber-600">${usage.total_cost}</p>
              </div>
            </div>
          )}

          {/* Providers */}
          <div className="space-y-6 mb-12">
            <h2 className="text-2xl font-bold text-gray-900">AI Providers</h2>
            
            {loading ? (
              <div className="text-center py-16">
                <div className="w-12 h-12 border-3 border-purple-200 border-t-purple-600 rounded-full animate-spin mx-auto"></div>
                <p className="text-gray-500 mt-4">Loading providers...</p>
              </div>
            ) : (
              <div className="grid gap-6">
                {providers.map((provider) => (
                  <div 
                    key={provider.id}
                    className={`bg-gradient-to-r ${providerColors[provider.id]} border rounded-3xl p-8 transition-all duration-300 hover:shadow-2xl hover:-translate-y-1`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-5">
                        <span className="text-5xl">{providerIcons[provider.id]}</span>
                        <div>
                          <h3 className="text-2xl font-bold text-gray-900">{provider.name}</h3>
                          <p className="text-gray-600 text-sm mt-1">
                            Models: {provider.models?.join(', ')}
                          </p>
                          {provider.has_key && (
                            <p className="text-green-600 text-sm mt-2 font-semibold flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-green-500"></span>
                              Key: •••••••{provider.key_hint}
                            </p>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        {provider.has_key ? (
                          <>
                            {/* Toggle Switch */}
                            <label className="relative inline-flex items-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={provider.is_active}
                                onChange={() => handleToggleKey(provider.id, provider.is_active)}
                                className="sr-only peer"
                              />
                              <div className="w-14 h-7 bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-green-500 shadow-inner"></div>
                            </label>
                            
                            {/* Update Key */}
                            <button
                              onClick={() => setAddingKey(provider.id)}
                              className="px-5 py-2.5 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl text-sm font-semibold text-gray-700 transition-all hover:shadow-lg"
                            >
                              Update
                            </button>
                            
                            {/* Delete Key */}
                            <button
                              onClick={() => handleDeleteKey(provider.id)}
                              className="px-5 py-2.5 bg-red-50 hover:bg-red-100 border border-red-200 text-red-600 rounded-xl text-sm font-semibold transition-all hover:shadow-lg"
                            >
                              Remove
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => setAddingKey(provider.id)}
                            className="px-8 py-3 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-violet-700 transition-all shadow-lg shadow-purple-300/50 hover:shadow-xl hover:scale-105"
                          >
                            + Add Key
                          </button>
                        )}
                      </div>
                    </div>
                    
                    {/* Add Key Form */}
                    {addingKey === provider.id && (
                      <div className="mt-6 p-6 bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200 shadow-xl">
                        <p className="text-sm text-gray-600 mb-4">
                          Get your API key from: <a href={provider.docs_url} target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:text-purple-700 font-semibold underline">{provider.docs_url}</a>
                        </p>
                        <div className="flex gap-3">
                          <input
                            type="password"
                            value={newKey}
                            onChange={(e) => setNewKey(e.target.value)}
                            placeholder={`Enter your ${provider.name} API key (${provider.key_prefix}...)`}
                            className="flex-1 px-5 py-3.5 bg-gray-50 border border-purple-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 text-gray-900"
                          />
                          <button
                            onClick={() => handleAddKey(provider.id)}
                            className="px-8 py-3.5 bg-green-600 hover:bg-green-700 text-white rounded-xl font-semibold transition-all shadow-lg hover:scale-105"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => { setAddingKey(null); setNewKey(''); }}
                            className="px-6 py-3.5 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-xl font-semibold transition-all"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                    
                    {/* Status Badge */}
                    {provider.has_key && (
                      <div className="mt-6 flex items-center gap-3 p-4 bg-white/80 backdrop-blur-sm rounded-xl border border-gray-200">
                        <span className={`w-3 h-3 rounded-full ${provider.is_active ? 'bg-green-500' : 'bg-gray-400'}`}></span>
                        <span className="text-sm text-gray-700 font-medium">
                          {provider.is_active ? 'Active - Will be used for AI generation' : 'Disabled - Using platform key'}
                        </span>
                        {provider.last_used && (
                          <span className="text-xs text-gray-500 ml-auto">
                            Last used: {new Date(provider.last_used).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Usage Table */}
          {usage && usage.recent_runs?.length > 0 && (
            <div className="bg-white/90 backdrop-blur-sm border border-purple-100 rounded-3xl p-8 shadow-xl shadow-purple-100/20">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent AI Usage</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-600 border-b border-purple-100">
                      <th className="pb-4 font-semibold">Provider</th>
                      <th className="pb-4 font-semibold">Model</th>
                      <th className="pb-4 font-semibold">Tokens</th>
                      <th className="pb-4 font-semibold">Cost</th>
                      <th className="pb-4 font-semibold">Source</th>
                      <th className="pb-4 font-semibold">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usage.recent_runs.map((run, i) => (
                      <tr key={run.id || i} className="border-b border-purple-50 hover:bg-purple-50/50 transition-colors">
                        <td className="py-4 capitalize font-medium text-gray-900">{run.provider}</td>
                        <td className="py-4 text-gray-600">{run.model}</td>
                        <td className="py-4 text-gray-900 font-semibold">{(run.tokens_in || 0) + (run.tokens_out || 0)}</td>
                        <td className="py-4 text-green-600 font-semibold">${run.cost_estimate}</td>
                        <td className="py-4">
                          <span className={`px-3 py-1.5 rounded-full text-xs font-bold ${run.is_byo_key ? 'bg-green-100 text-green-700' : 'bg-purple-100 text-purple-700'}`}>
                            {run.is_byo_key ? 'Your Key' : 'Platform'}
                          </span>
                        </td>
                        <td className="py-4 text-gray-500">{new Date(run.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Info Box */}
          <div className="mt-12 p-8 bg-gradient-to-r from-purple-50 to-violet-50 border border-purple-200 rounded-3xl">
            <h3 className="text-xl font-bold text-purple-900 mb-4 flex items-center gap-2">
              <span>🔒</span>
              Security & Privacy
            </h3>
            <ul className="text-gray-700 space-y-2 leading-relaxed">
              <li className="flex items-start gap-3">
                <span className="text-purple-600 mt-1">✓</span>
                <span>Your API keys are encrypted using AES-256 before storage</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-purple-600 mt-1">✓</span>
                <span>Keys are never exposed in API responses (only last 4 chars shown)</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-purple-600 mt-1">✓</span>
                <span>You can disable keys anytime without deleting them</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-purple-600 mt-1">✓</span>
                <span>When your key is active, it will be used instead of platform credits</span>
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AIKeys;
