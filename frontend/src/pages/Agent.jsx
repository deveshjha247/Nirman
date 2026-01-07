import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import CodingAgent from '../components/CodingAgent';
import Sidebar from '../components/Sidebar';
import { Button } from '../components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import {
  Bot,
  Code,
  Brain,
  Globe,
  FileCode,
  Zap,
  TrendingUp,
  Clock,
  CreditCard,
  BarChart3,
  Settings,
  MessageSquare,
  History,
  Sparkles,
} from 'lucide-react';

export default function Agent() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  const [status, setStatus] = useState(null);
  const [usageHistory, setUsageHistory] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [plans, setPlans] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);

  useEffect(() => {
    fetchStatus();
    fetchUsageHistory();
    fetchConversations();
    fetchPlans();
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await api.get('/api/agent/status');
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  };

  const fetchUsageHistory = async () => {
    try {
      const response = await api.get('/api/agent/usage/history?days=30');
      setUsageHistory(response.data);
    } catch (error) {
      console.error('Failed to fetch usage history:', error);
    }
  };

  const fetchConversations = async () => {
    try {
      const response = await api.get('/api/agent/conversations?limit=10');
      setConversations(response.data.conversations || []);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    }
  };

  const fetchPlans = async () => {
    try {
      const response = await api.get('/api/agent/plans');
      setPlans(response.data.plans || []);
    } catch (error) {
      console.error('Failed to fetch plans:', error);
    }
  };

  return (
    <div className="flex h-screen bg-gray-950">
      <Sidebar />
      
      <div className="flex-1 overflow-hidden">
        {/* Header */}
        <div className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl shadow-lg shadow-purple-500/20">
                  <Bot className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white">Coding Agent</h1>
                  <p className="text-gray-400">
                    AI-powered coding assistant with intelligent task routing
                  </p>
                </div>
              </div>
              
              {status && (
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-sm text-gray-400">Plan</div>
                    <Badge className="bg-gradient-to-r from-purple-600 to-blue-600 text-white">
                      {status.plan.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-400">Today</div>
                    <div className="text-lg font-semibold text-white">
                      {status.requests_today} / {status.daily_limit === -1 ? '∞' : status.daily_limit}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Tabs */}
          <div className="px-6">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="bg-transparent border-b border-gray-800 rounded-none">
                <TabsTrigger 
                  value="chat"
                  className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-purple-500 rounded-none"
                >
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Chat
                </TabsTrigger>
                <TabsTrigger 
                  value="history"
                  className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-purple-500 rounded-none"
                >
                  <History className="w-4 h-4 mr-2" />
                  History
                </TabsTrigger>
                <TabsTrigger 
                  value="usage"
                  className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-purple-500 rounded-none"
                >
                  <BarChart3 className="w-4 h-4 mr-2" />
                  Usage
                </TabsTrigger>
                <TabsTrigger 
                  value="plans"
                  className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-purple-500 rounded-none"
                >
                  <CreditCard className="w-4 h-4 mr-2" />
                  Plans
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>

        {/* Content */}
        <div className="h-[calc(100vh-180px)]">
          {activeTab === 'chat' && (
            <CodingAgent projectId={selectedProject} />
          )}

          {activeTab === 'history' && (
            <div className="p-6 overflow-y-auto h-full">
              <h2 className="text-xl font-semibold text-white mb-4">Conversation History</h2>
              
              {conversations.length === 0 ? (
                <Card className="bg-gray-900 border-gray-800">
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <History className="w-12 h-12 text-gray-600 mb-4" />
                    <p className="text-gray-400">No conversations yet</p>
                    <Button
                      variant="outline"
                      className="mt-4 border-gray-700"
                      onClick={() => setActiveTab('chat')}
                    >
                      Start a conversation
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {conversations.map((conv) => (
                    <Card 
                      key={conv.id}
                      className="bg-gray-900 border-gray-800 hover:border-gray-700 cursor-pointer transition-colors"
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="text-white line-clamp-2">{conv.preview}</p>
                            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                              <span className="flex items-center gap-1">
                                <MessageSquare className="w-3 h-3" />
                                {conv.message_count} messages
                              </span>
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {new Date(conv.updated_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'usage' && (
            <div className="p-6 overflow-y-auto h-full">
              <h2 className="text-xl font-semibold text-white mb-4">Usage Statistics</h2>
              
              {/* Stats Cards */}
              {status && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <Card className="bg-gray-900 border-gray-800">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-400">Total Requests</p>
                          <p className="text-2xl font-bold text-white">{status.total_requests}</p>
                        </div>
                        <TrendingUp className="w-8 h-8 text-green-500" />
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-gray-900 border-gray-800">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-400">Tokens Used</p>
                          <p className="text-2xl font-bold text-white">
                            {(status.total_tokens_used / 1000).toFixed(1)}K
                          </p>
                        </div>
                        <Zap className="w-8 h-8 text-yellow-500" />
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-gray-900 border-gray-800">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-400">Total Cost</p>
                          <p className="text-2xl font-bold text-white">
                            ${status.total_cost.toFixed(4)}
                          </p>
                        </div>
                        <CreditCard className="w-8 h-8 text-purple-500" />
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-gray-900 border-gray-800">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-400">Remaining Today</p>
                          <p className="text-2xl font-bold text-white">
                            {status.requests_remaining === 'unlimited' ? '∞' : status.requests_remaining}
                          </p>
                        </div>
                        <Clock className="w-8 h-8 text-blue-500" />
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
              
              {/* Usage by Provider */}
              {usageHistory?.by_provider && (
                <Card className="bg-gray-900 border-gray-800">
                  <CardHeader>
                    <CardTitle className="text-white">Usage by Provider</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {usageHistory.by_provider.map((provider) => (
                        <div key={provider.provider} className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-600 to-blue-600 flex items-center justify-center">
                              <span className="text-xs text-white font-bold">
                                {provider.provider?.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <span className="text-white">{provider.provider}</span>
                          </div>
                          <div className="text-right">
                            <p className="text-white">{provider.requests} requests</p>
                            <p className="text-xs text-gray-500">
                              {(provider.tokens / 1000).toFixed(1)}K tokens • ${provider.cost.toFixed(4)}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {activeTab === 'plans' && (
            <div className="p-6 overflow-y-auto h-full">
              <h2 className="text-xl font-semibold text-white mb-4">Available Plans</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {plans.map((plan) => (
                  <Card 
                    key={plan.id}
                    className={`bg-gray-900 border-gray-800 ${
                      status?.plan === plan.id ? 'ring-2 ring-purple-500' : ''
                    }`}
                  >
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-white">{plan.name}</CardTitle>
                        {status?.plan === plan.id && (
                          <Badge className="bg-purple-600">Current</Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center gap-2 text-sm">
                          <Clock className="w-4 h-4 text-gray-500" />
                          <span className="text-gray-300">
                            {plan.daily_limit === 'Unlimited' ? '∞' : plan.daily_limit} requests/day
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <Zap className="w-4 h-4 text-gray-500" />
                          <span className="text-gray-300">
                            {(plan.max_tokens / 1000)}K max tokens
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <Code className="w-4 h-4 text-gray-500" />
                          <span className="text-gray-300">
                            {plan.providers_count} providers
                          </span>
                        </div>
                        
                        <div className="pt-3 border-t border-gray-800">
                          <p className="text-xs text-gray-500 mb-2">Providers:</p>
                          <div className="flex flex-wrap gap-1">
                            {plan.allowed_providers.slice(0, 4).map((p) => (
                              <Badge 
                                key={p} 
                                variant="outline"
                                className="text-xs border-gray-700 text-gray-400"
                              >
                                {p}
                              </Badge>
                            ))}
                            {plan.allowed_providers.length > 4 && (
                              <Badge 
                                variant="outline"
                                className="text-xs border-gray-700 text-gray-400"
                              >
                                +{plan.allowed_providers.length - 4} more
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
