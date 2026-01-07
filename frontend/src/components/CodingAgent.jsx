import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './ui/card';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';
import { 
  Send, 
  Bot, 
  User, 
  Code, 
  Loader2, 
  Copy, 
  Check, 
  Settings, 
  Zap,
  Brain,
  Globe,
  FileCode,
  MessageSquare,
  Sparkles,
  ChevronDown,
  Terminal,
  RefreshCw
} from 'lucide-react';

// Agent type icons
const AGENT_ICONS = {
  coder: Code,
  planner: Brain,
  browser: Globe,
  file: FileCode,
  casual: MessageSquare,
};

// Provider colors
const PROVIDER_COLORS = {
  openai: 'bg-green-500',
  gemini: 'bg-blue-500',
  claude: 'bg-purple-500',
  deepseek: 'bg-cyan-500',
  groq: 'bg-orange-500',
  mistral: 'bg-red-500',
};

export default function CodingAgent({ projectId }) {
  const { user } = useAuth();
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [availableModels, setAvailableModels] = useState(null);
  const [availableAgents, setAvailableAgents] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState('auto');
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState('auto');
  const [conversationId, setConversationId] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef(null);

  // Fetch agent status and models on mount
  useEffect(() => {
    fetchStatus();
    fetchModels();
    fetchAgents();
  }, []);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchStatus = async () => {
    try {
      const response = await api.get('/api/agent/status');
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch agent status:', error);
    }
  };

  const fetchModels = async () => {
    try {
      const response = await api.get('/api/agent/models');
      setAvailableModels(response.data);
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const fetchAgents = async () => {
    try {
      const response = await api.get('/api/agent/agents');
      setAvailableAgents(response.data.agents || []);
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    }
  };

  const sendMessage = async () => {
    if (!prompt.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: prompt,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setPrompt('');
    setIsLoading(true);

    try {
      // Use direct process endpoint for single requests with agent selection
      const response = await api.post('/api/agent/process', {
        prompt: prompt,
        project_id: projectId,
        provider: selectedProvider,
        model: selectedModel,
        agent_type: selectedAgent === 'auto' ? null : selectedAgent,
      });

      if (response.data.success) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: response.data.answer,
          timestamp: new Date().toISOString(),
          agent_type: response.data.agent_type,
          code_blocks: response.data.code_blocks || [],
        }]);
        // Refresh status to update usage
        fetchStatus();
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${response.data.error || 'Unknown error'}`,
          timestamp: new Date().toISOString(),
          isError: true,
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date().toISOString(),
        isError: true,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const copyCode = (code, index) => {
    navigator.clipboard.writeText(code);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const newConversation = () => {
    setMessages([]);
    setConversationId(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Render code block with syntax highlighting
  const renderCodeBlock = (block, index) => {
    const language = block.language || 'text';
    const filename = block.filename;
    
    return (
      <div key={index} className="my-3 rounded-lg overflow-hidden border border-gray-700">
        <div className="flex items-center justify-between bg-gray-800 px-4 py-2">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-300">{language}</span>
            {filename && (
              <span className="text-sm text-gray-500">• {filename}</span>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => copyCode(block.code, index)}
            className="text-gray-400 hover:text-white"
          >
            {copiedIndex === index ? (
              <Check className="w-4 h-4" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </Button>
        </div>
        <pre className="p-4 bg-gray-900 overflow-x-auto">
          <code className="text-sm text-gray-100">{block.code}</code>
        </pre>
      </div>
    );
  };

  // Render message content (handles code blocks)
  const renderMessageContent = (message) => {
    const content = message.content;
    const codeBlocks = message.code_blocks || [];
    
    // If there are code blocks, render them specially
    if (codeBlocks.length > 0) {
      // Split content by code blocks and render
      return (
        <div>
          <div className="whitespace-pre-wrap">{content.split(/```[\s\S]*?```/).join('')}</div>
          {codeBlocks.map((block, idx) => renderCodeBlock(block, idx))}
        </div>
      );
    }
    
    // Check for inline code blocks
    const parts = content.split(/(```[\s\S]*?```)/g);
    
    return (
      <div>
        {parts.map((part, idx) => {
          if (part.startsWith('```') && part.endsWith('```')) {
            const match = part.match(/```(\w+)?\n?([\s\S]*?)```/);
            if (match) {
              return renderCodeBlock({
                language: match[1] || 'text',
                code: match[2].trim(),
              }, idx);
            }
          }
          return <div key={idx} className="whitespace-pre-wrap">{part}</div>;
        })}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Header */}
      <div className="border-b border-gray-800 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Coding Agent</h2>
              <p className="text-sm text-gray-400">
                {selectedAgent === 'auto' 
                  ? 'Smart routing enabled' 
                  : `Using ${availableAgents.find(a => a.id === selectedAgent)?.name || selectedAgent}`}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Status Badge */}
            {status && (
              <Badge 
                variant="outline" 
                className="text-xs border-gray-700 text-gray-300"
              >
                {status.requests_remaining === 'unlimited' 
                  ? '∞ Requests' 
                  : `${status.requests_remaining} left today`}
              </Badge>
            )}
            
            {/* New Chat */}
            <Button
              variant="outline"
              size="sm"
              onClick={newConversation}
              className="border-gray-700 text-gray-300 hover:bg-gray-800"
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              New
            </Button>
            
            {/* Settings Toggle */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSettings(!showSettings)}
              className="border-gray-700 text-gray-300 hover:bg-gray-800"
            >
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>
        
        {/* Settings Panel */}
        {showSettings && availableModels && (
          <div className="mt-4 p-4 bg-gray-900 rounded-lg border border-gray-800">
            <h3 className="text-sm font-medium text-gray-300 mb-3">Agent & Model Settings</h3>
            
            {/* Agent Selection */}
            <div className="mb-4">
              <label className="block text-xs text-gray-500 mb-2">Select Agent</label>
              <div className="grid grid-cols-3 gap-2">
                {availableAgents.map(agent => (
                  <button
                    key={agent.id}
                    onClick={() => setSelectedAgent(agent.id)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      selectedAgent === agent.id
                        ? 'border-purple-500 bg-purple-500/10'
                        : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{agent.icon}</span>
                      <span className="text-sm font-medium text-white">{agent.name}</span>
                    </div>
                    <p className="text-xs text-gray-500 line-clamp-2">{agent.description}</p>
                  </button>
                ))}
              </div>
              {selectedAgent !== 'auto' && availableAgents.find(a => a.id === selectedAgent) && (
                <div className="mt-2 p-2 bg-gray-800 rounded text-xs text-gray-400">
                  <span className="text-purple-400">Capabilities: </span>
                  {availableAgents.find(a => a.id === selectedAgent)?.capabilities?.join(', ')}
                </div>
              )}
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              {/* Provider Selection */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">Provider</label>
                <select
                  value={selectedProvider}
                  onChange={(e) => {
                    setSelectedProvider(e.target.value);
                    setSelectedModel(null);
                  }}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-sm text-gray-300"
                >
                  <option value="auto">Auto (Recommended)</option>
                  {Object.keys(availableModels.providers || {}).map(provider => (
                    <option key={provider} value={provider}>
                      {provider.charAt(0).toUpperCase() + provider.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* Model Selection */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">Model</label>
                <select
                  value={selectedModel || ''}
                  onChange={(e) => setSelectedModel(e.target.value || null)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-sm text-gray-300"
                  disabled={selectedProvider === 'auto'}
                >
                  <option value="">Default</option>
                  {selectedProvider !== 'auto' && 
                    availableModels.providers[selectedProvider]?.models.map(model => (
                      <option key={model} value={model}>{model}</option>
                    ))
                  }
                </select>
              </div>
            </div>
            
            {/* Current Plan Info */}
            {status && (
              <div className="mt-4 pt-4 border-t border-gray-800">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Plan</span>
                  <Badge className="bg-gradient-to-r from-purple-600 to-blue-600">
                    {status.plan.toUpperCase()}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-sm mt-2">
                  <span className="text-gray-500">Default Model</span>
                  <span className="text-gray-300">{status.default_model}</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="p-4 bg-gradient-to-r from-purple-600/20 to-blue-600/20 rounded-full mb-4">
              <Sparkles className="w-12 h-12 text-purple-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              {selectedAgent === 'auto' ? 'Start a Conversation' : `${availableAgents.find(a => a.id === selectedAgent)?.name || 'Agent'} Ready`}
            </h3>
            <p className="text-gray-400 max-w-md mb-6">
              {selectedAgent === 'coder' && 'Ask me to write code, create functions, build APIs, or debug issues.'}
              {selectedAgent === 'browser' && 'Ask me to research topics, find documentation, or search the web.'}
              {selectedAgent === 'file' && 'Ask me to create, read, or manage files in your project.'}
              {selectedAgent === 'planner' && 'Ask me to plan complex projects and break them into tasks.'}
              {selectedAgent === 'casual' && 'Ask me anything - general questions, explanations, or casual chat.'}
              {selectedAgent === 'auto' && "Ask me anything and I'll automatically select the best approach for your task."}
            </p>
            
            {/* Quick Prompts - Agent Specific */}
            <div className="grid grid-cols-2 gap-2 max-w-lg">
              {(selectedAgent === 'auto' ? [
                'Create a React todo app',
                'Build a REST API with FastAPI',
                'Write a Python web scraper',
                'Make a responsive landing page',
              ] : selectedAgent === 'coder' ? [
                'Write a sorting algorithm',
                'Create a React component',
                'Build a CRUD API',
                'Debug this code snippet',
              ] : selectedAgent === 'browser' ? [
                'Research React best practices',
                'Find FastAPI documentation',
                'Search for authentication patterns',
                'Look up latest Python features',
              ] : selectedAgent === 'file' ? [
                'Create a new config file',
                'Read package.json',
                'List all Python files',
                'Create project structure',
              ] : selectedAgent === 'planner' ? [
                'Plan an e-commerce app',
                'Design a todo app architecture',
                'Break down a chat application',
                'Create project roadmap',
              ] : [
                'What is machine learning?',
                'Explain REST vs GraphQL',
                'How does React work?',
                'What is clean code?',
              ]).map((suggestion, idx) => (
                <Button
                  key={idx}
                  variant="outline"
                  size="sm"
                  onClick={() => setPrompt(suggestion)}
                  className="text-left justify-start border-gray-700 text-gray-300 hover:bg-gray-800"
                >
                  <Zap className="w-4 h-4 mr-2 text-yellow-500" />
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message, idx) => (
              <div
                key={idx}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`flex gap-3 max-w-[85%] ${
                    message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                  }`}
                >
                  {/* Avatar */}
                  <div
                    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      message.role === 'user'
                        ? 'bg-blue-600'
                        : message.isError
                        ? 'bg-red-600'
                        : 'bg-gradient-to-r from-purple-600 to-blue-600'
                    }`}
                  >
                    {message.role === 'user' ? (
                      <User className="w-4 h-4 text-white" />
                    ) : message.agent_type ? (
                      (() => {
                        const Icon = AGENT_ICONS[message.agent_type] || Bot;
                        return <Icon className="w-4 h-4 text-white" />;
                      })()
                    ) : (
                      <Bot className="w-4 h-4 text-white" />
                    )}
                  </div>
                  
                  {/* Message Content */}
                  <div
                    className={`rounded-lg px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : message.isError
                        ? 'bg-red-900/50 border border-red-800 text-red-200'
                        : 'bg-gray-800 text-gray-100'
                    }`}
                  >
                    {message.agent_type && (
                      <div className="flex items-center gap-2 mb-2">
                        <Badge 
                          variant="outline" 
                          className="text-xs border-gray-600 text-gray-400"
                        >
                          {message.agent_type} agent
                        </Badge>
                      </div>
                    )}
                    {renderMessageContent(message)}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-r from-purple-600 to-blue-600 flex items-center justify-center">
                    {(() => {
                      const Icon = selectedAgent !== 'auto' ? AGENT_ICONS[selectedAgent] : Bot;
                      return <Icon className="w-4 h-4 text-white" />;
                    })()}
                  </div>
                  <div className="bg-gray-800 rounded-lg px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                      <span className="text-gray-400">
                        {selectedAgent === 'auto' 
                          ? 'Routing & Processing...' 
                          : `${availableAgents.find(a => a.id === selectedAgent)?.name || 'Agent'} working...`}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-gray-800 p-4">
        <div className="flex gap-2">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me to code something..."
            className="flex-1 px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 resize-none focus:outline-none focus:border-purple-500 transition-colors"
            rows={2}
            disabled={isLoading}
          />
          <Button
            onClick={sendMessage}
            disabled={!prompt.trim() || isLoading}
            className="px-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </Button>
        </div>
        
        {/* Footer Info */}
        <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
          <span>Press Enter to send, Shift+Enter for new line</span>
          {status && (
            <span>
              {status.total_requests} total requests • ${status.total_cost.toFixed(4)} spent
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
