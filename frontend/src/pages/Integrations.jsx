import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { integrationsAPI } from '../lib/api';
import Sidebar from '../components/Sidebar';

const Integrations = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(null);
  const [repos, setRepos] = useState([]);
  const [showRepos, setShowRepos] = useState(false);
  const [reposLoading, setReposLoading] = useState(false);
  
  // Handle OAuth callback
  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    
    if (code && state) {
      handleGitHubCallback(code, state);
    }
  }, [searchParams]);
  
  const handleGitHubCallback = async (code, state) => {
    try {
      setConnecting('github');
      const response = await integrationsAPI.githubCallback(code, state);
      alert(response.data.message);
      // Clean URL
      navigate('/integrations', { replace: true });
      fetchIntegrations();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to connect GitHub');
    } finally {
      setConnecting(null);
    }
  };
  
  const fetchIntegrations = async () => {
    try {
      const response = await integrationsAPI.getIntegrations();
      setIntegrations(response.data.integrations);
    } catch (error) {
      console.error('Failed to fetch integrations:', error);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchIntegrations();
  }, []);
  
  const connectGitHub = async () => {
    try {
      setConnecting('github');
      const response = await integrationsAPI.getGitHubAuthUrl();
      window.location.href = response.data.auth_url;
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to get GitHub auth URL');
      setConnecting(null);
    }
  };
  
  const disconnectGitHub = async () => {
    if (!window.confirm('Are you sure you want to disconnect GitHub?')) return;
    
    try {
      await integrationsAPI.disconnectGitHub();
      fetchIntegrations();
      setShowRepos(false);
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to disconnect');
    }
  };
  
  const loadRepos = async () => {
    try {
      setReposLoading(true);
      const response = await integrationsAPI.listRepos();
      setRepos(response.data.repos);
      setShowRepos(true);
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to load repos');
    } finally {
      setReposLoading(false);
    }
  };
  
  const integrationIcons = {
    github: '🐙',
    vercel: '▲',
    netlify: '◆',
    supabase: '⚡',
    firebase: '🔥'
  };
  
  const integrationColors = {
    github: 'from-gray-800 to-gray-900',
    vercel: 'from-gray-900 to-black',
    netlify: 'from-teal-500 to-teal-600',
    supabase: 'from-green-500 to-emerald-600',
    firebase: 'from-orange-400 to-orange-500'
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 flex">
      <Sidebar active="integrations" />
      
      <main className="flex-1 p-8 overflow-auto">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
              <span className="text-4xl">🔗</span>
              App Integrations
            </h1>
            <p className="text-gray-600">
              Connect your favorite services to push code, deploy, and more
            </p>
          </div>
          
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-gray-800"></div>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {integrations.map((integration) => (
                <div
                  key={integration.id}
                  className={`relative rounded-2xl border-2 p-6 transition-all ${
                    integration.connected
                      ? 'border-green-200 bg-green-50/50'
                      : integration.coming_soon
                      ? 'border-gray-100 bg-gray-50/50 opacity-60'
                      : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-lg'
                  }`}
                >
                  {/* Coming Soon Badge */}
                  {integration.coming_soon && (
                    <span className="absolute top-4 right-4 px-2 py-1 bg-gray-200 text-gray-600 text-xs font-medium rounded-full">
                      Coming Soon
                    </span>
                  )}
                  
                  {/* Connected Badge */}
                  {integration.connected && (
                    <span className="absolute top-4 right-4 px-2 py-1 bg-green-500 text-white text-xs font-medium rounded-full flex items-center gap-1">
                      <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span>
                      Connected
                    </span>
                  )}
                  
                  {/* Icon */}
                  <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${integrationColors[integration.id] || 'from-gray-500 to-gray-600'} flex items-center justify-center text-white text-2xl mb-4`}>
                    {integrationIcons[integration.id] || '🔌'}
                  </div>
                  
                  {/* Name & Description */}
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">{integration.name}</h3>
                  <p className="text-gray-600 text-sm mb-4">{integration.description}</p>
                  
                  {/* Features */}
                  <div className="flex flex-wrap gap-2 mb-6">
                    {integration.features?.map((feature, i) => (
                      <span key={i} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                        {feature}
                      </span>
                    ))}
                  </div>
                  
                  {/* Connected User */}
                  {integration.connected && integration.username && (
                    <div className="flex items-center gap-3 mb-4 p-3 bg-white rounded-lg border border-gray-100">
                      {integration.avatar && (
                        <img src={integration.avatar} alt="" className="w-8 h-8 rounded-full" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">@{integration.username}</p>
                        <p className="text-xs text-gray-500">Connected</p>
                      </div>
                    </div>
                  )}
                  
                  {/* Actions */}
                  {!integration.coming_soon && (
                    <div className="flex gap-2">
                      {integration.connected ? (
                        <>
                          {integration.id === 'github' && (
                            <button
                              onClick={loadRepos}
                              disabled={reposLoading}
                              className="flex-1 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 transition-all disabled:opacity-50"
                            >
                              {reposLoading ? 'Loading...' : 'View Repos'}
                            </button>
                          )}
                          <button
                            onClick={integration.id === 'github' ? disconnectGitHub : undefined}
                            className="px-4 py-2 border border-red-200 text-red-600 rounded-lg text-sm font-medium hover:bg-red-50 transition-all"
                          >
                            Disconnect
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={integration.id === 'github' ? connectGitHub : undefined}
                          disabled={connecting === integration.id}
                          className="w-full px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                          {connecting === integration.id ? (
                            <>
                              <span className="animate-spin">⏳</span>
                              Connecting...
                            </>
                          ) : (
                            <>Connect {integration.name}</>
                          )}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          
          {/* Repos Modal */}
          {showRepos && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-900">Your GitHub Repositories</h2>
                  <button
                    onClick={() => setShowRepos(false)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-all"
                  >
                    ✕
                  </button>
                </div>
                <div className="p-6 overflow-auto max-h-[60vh]">
                  {repos.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">No repositories found</p>
                  ) : (
                    <div className="space-y-3">
                      {repos.map((repo) => (
                        <div
                          key={repo.id}
                          className="p-4 border border-gray-200 rounded-xl hover:border-gray-300 transition-all"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <a
                                  href={repo.html_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 font-medium hover:underline truncate"
                                >
                                  {repo.name}
                                </a>
                                {repo.private && (
                                  <span className="px-1.5 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded">
                                    Private
                                  </span>
                                )}
                              </div>
                              {repo.description && (
                                <p className="text-gray-600 text-sm truncate">{repo.description}</p>
                              )}
                              <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                                {repo.language && (
                                  <span className="flex items-center gap-1">
                                    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                                    {repo.language}
                                  </span>
                                )}
                                <span>Updated {new Date(repo.updated_at).toLocaleDateString()}</span>
                              </div>
                            </div>
                            <a
                              href={repo.html_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 transition-all"
                            >
                              Open →
                            </a>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {/* How It Works */}
          <div className="mt-12 p-6 bg-gradient-to-r from-gray-900 to-gray-800 rounded-2xl text-white">
            <h3 className="text-xl font-semibold mb-4">🚀 How GitHub Integration Works</h3>
            <div className="grid md:grid-cols-3 gap-6">
              <div>
                <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center text-lg mb-3">1</div>
                <h4 className="font-medium mb-1">Connect GitHub</h4>
                <p className="text-gray-400 text-sm">Authorize Nirman to access your GitHub repositories</p>
              </div>
              <div>
                <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center text-lg mb-3">2</div>
                <h4 className="font-medium mb-1">Build Your Website</h4>
                <p className="text-gray-400 text-sm">Create beautiful websites using AI in the Builder</p>
              </div>
              <div>
                <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center text-lg mb-3">3</div>
                <h4 className="font-medium mb-1">Deploy with One Click</h4>
                <p className="text-gray-400 text-sm">Push to GitHub & enable GitHub Pages automatically</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Integrations;
