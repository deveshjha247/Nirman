import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Sidebar = ({ active }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  
  const menuItems = [
    { id: 'projects', icon: '📁', label: 'Projects', path: '/dashboard' },
    { id: 'chat', icon: '💬', label: 'AI Chat', path: '/chat', highlight: true },
    { id: 'agent', icon: '🤖', label: 'Coding Agent', path: '/agent' },
    { id: 'ai-keys', icon: '🔑', label: 'AI Keys', path: '/ai-keys' },
    { id: 'integrations', icon: '🔗', label: 'Integrations', path: '/integrations' },
    { id: 'wallet', icon: '💰', label: 'Wallet', path: '/wallet' },
    { id: 'plans', icon: '⭐', label: 'Plans', path: '/plans' },
    { id: 'referrals', icon: '👥', label: 'Referrals', path: '/referrals' },
    { id: 'settings', icon: '⚙️', label: 'Settings', path: '/settings' },
  ];
  
  if (user?.is_admin) {
    menuItems.push({ id: 'admin', icon: '🔐', label: 'Admin', path: '/admin' });
  }
  
  return (
    <aside className="w-72 bg-white/90 backdrop-blur-xl border-r border-purple-100/80 min-h-screen flex flex-col shadow-xl shadow-purple-100/20">
      {/* Logo Header */}
      <div className="p-6 border-b border-purple-100/60">
        <div className="flex items-center gap-3 cursor-pointer group" onClick={() => navigate('/')}>
          <img src="/logo.png" alt="Nirman Logo" className="w-11 h-11 rounded-xl shadow-lg shadow-purple-300/50 group-hover:shadow-xl group-hover:scale-105 transition-all duration-200" />
          <span className="text-xl font-bold text-gray-900">Nirman</span>
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 p-4">
        <p className="px-4 py-2 text-xs font-semibold text-purple-400 uppercase tracking-wider">Menu</p>
        <ul className="space-y-1.5 mt-2">
          {menuItems.map(item => (
            <li key={item.id}>
              <button
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-200 ${
                  active === item.id
                    ? 'bg-gradient-to-r from-purple-600 to-violet-600 text-white shadow-lg shadow-purple-300/50'
                    : 'text-gray-600 hover:bg-purple-50 hover:text-purple-700'
                }`}
                data-testid={`nav-${item.id}`}
              >
                <span className="text-xl">{item.icon}</span>
                <span className="font-semibold">{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
      
      {/* User Section */}
      <div className="p-4 border-t border-purple-100/60 bg-gradient-to-b from-white to-purple-50/30">
        <div className="flex items-center gap-3 mb-4 p-3.5 bg-white/90 backdrop-blur-sm rounded-xl border border-purple-100 shadow-lg shadow-purple-100/20">
          <div className="w-11 h-11 rounded-full bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center text-white font-bold shadow-lg shadow-purple-300/50">
            {user?.name?.charAt(0)?.toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-gray-900 truncate">{user?.name}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
          <span className={`px-2.5 py-1.5 text-xs font-bold rounded-full ${
            user?.plan === 'enterprise' ? 'bg-gradient-to-r from-amber-400 to-orange-500 text-white shadow-md' :
            user?.plan === 'pro' ? 'bg-gradient-to-r from-purple-500 to-violet-600 text-white shadow-md' :
            'bg-gray-100 text-gray-600'
          }`}>
            {user?.plan?.toUpperCase()}
          </span>
        </div>
        <button
          onClick={logout}
          className="w-full px-4 py-3 text-sm text-gray-600 hover:text-purple-700 hover:bg-purple-50 rounded-xl transition-all duration-200 font-semibold"
          data-testid="logout-btn"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
