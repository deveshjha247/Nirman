import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { projectsAPI, chatAPI, integrationsAPI } from '../lib/api';

const Builder = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { projectId } = useParams();
  const [searchParams] = useSearchParams();
  const templatePrompt = searchParams.get('prompt');
  const messagesEndRef = useRef(null);
  
  const [project, setProject] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiProvider, setAiProvider] = useState('openai');
  const [generatedCode, setGeneratedCode] = useState('');
  const [activeTab, setActiveTab] = useState('preview');
  const [projectLoading, setProjectLoading] = useState(true);
  const [generationsUsed, setGenerationsUsed] = useState(0);
  const [generationsLimit, setGenerationsLimit] = useState(100);
  
  // Auto Mode States
  const [autoMode, setAutoMode] = useState(false);
  const [autoSteps, setAutoSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [isAutoRunning, setIsAutoRunning] = useState(false);
  
  // GitHub Deploy States
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [deployLoading, setDeployLoading] = useState(false);
  const [deployStatus, setDeployStatus] = useState(null);
  const [githubConnected, setGithubConnected] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // Check GitHub connection status
  useEffect(() => {
    const checkGitHubStatus = async () => {
      try {
        const response = await integrationsAPI.getGitHubStatus();
        setGithubConnected(response.data.connected);
      } catch (error) {
        setGithubConnected(false);
      }
    };
    checkGitHubStatus();
  }, []);

  const fetchProject = async () => {
    try {
      const response = await projectsAPI.getProject(projectId);
      setProject(response.data);
      if (response.data.html_code) setGeneratedCode(response.data.html_code);
    } catch (error) {
      navigate('/dashboard');
    } finally {
      setProjectLoading(false);
    }
  };

  const fetchChatHistory = async () => {
    try {
      const response = await chatAPI.getHistory(projectId);
      setMessages(response.data);
      const lastAssistant = [...response.data].reverse().find(m => m.role === 'assistant');
      if (lastAssistant?.code_generated) setGeneratedCode(lastAssistant.code_generated);
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
    }
  };

  // Auto Mode: Analyze user request and create build plan
  const analyzeAndPlan = async (userRequest) => {
    const planPrompt = `Analyze this request and create a step-by-step build plan. Return ONLY a JSON array of steps.
    
Request: "${userRequest}"

Return format (JSON array only, no markdown):
[
  {"step": 1, "title": "Step title", "description": "What to do", "prompt": "Actual prompt for AI to execute"},
  ...
]

Create 3-5 steps to build this completely. Each step should build on previous work.`;

    try {
      const response = await chatAPI.sendMessage(projectId, planPrompt, aiProvider);
      const planText = response.data.message;
      
      // Extract JSON from response
      const jsonMatch = planText.match(/\[[\s\S]*\]/);
      if (jsonMatch) {
        const steps = JSON.parse(jsonMatch[0]);
        return steps;
      }
      throw new Error('Could not parse plan');
    } catch (error) {
      // Fallback to single step
      return [
        { step: 1, title: 'Build Complete App', description: 'Create the full application', prompt: userRequest }
      ];
    }
  };

  // Auto Mode: Execute a single step
  const executeStep = async (step, previousCode = '') => {
    const enhancedPrompt = previousCode 
      ? `${step.prompt}\n\nBuild upon this existing code:\n\`\`\`html\n${previousCode}\n\`\`\``
      : step.prompt;
    
    try {
      const response = await chatAPI.sendMessage(projectId, enhancedPrompt, aiProvider);
      return response.data.message;
    } catch (error) {
      throw error;
    }
  };

  // Auto Mode: Run all steps automatically
  const runAutoMode = async (userRequest) => {
    setIsAutoRunning(true);
    setAutoSteps([]);
    setCurrentStep(0);

    // Add system message
    setMessages(prev => [...prev, {
      role: 'system',
      content: '🤖 Auto Mode activated! Analyzing your request...',
      id: Date.now()
    }]);

    try {
      // Step 1: Plan
      const steps = await analyzeAndPlan(userRequest);
      setAutoSteps(steps);

      setMessages(prev => [...prev, {
        role: 'system',
        content: `📋 Created ${steps.length} step plan:\n${steps.map((s, i) => `${i + 1}. ${s.title}`).join('\n')}`,
        id: Date.now()
      }]);

      let currentCode = extractCodeFromResponse(generatedCode);

      // Execute each step
      for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        setCurrentStep(i + 1);

        setMessages(prev => [...prev, {
          role: 'system',
          content: `⚙️ Step ${i + 1}/${steps.length}: ${step.title}`,
          id: Date.now()
        }]);

        // Choose best AI for this step
        const bestAI = chooseBestAI(step);
        setAiProvider(bestAI);

        setMessages(prev => [...prev, {
          role: 'user',
          content: step.prompt,
          id: Date.now()
        }]);

        setLoading(true);
        const result = await executeStep(step, currentCode);
        setLoading(false);

        setMessages(prev => [...prev, {
          role: 'assistant',
          content: result,
          id: Date.now()
        }]);

        // Extract and save code
        const newCode = extractCodeFromResponse(result);
        if (newCode) {
          currentCode = newCode;
          setGeneratedCode(result);
        }

        // Small delay between steps
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      setMessages(prev => [...prev, {
        role: 'system',
        content: '✅ Auto Mode completed! Your app is ready.',
        id: Date.now()
      }]);

    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'system',
        content: `❌ Auto Mode error: ${error.message}`,
        id: Date.now()
      }]);
    } finally {
      setIsAutoRunning(false);
      setCurrentStep(0);
    }
  };

  // Choose best AI based on task type
  const chooseBestAI = (step) => {
    const prompt = step.prompt.toLowerCase();
    
    if (prompt.includes('design') || prompt.includes('ui') || prompt.includes('beautiful') || prompt.includes('style')) {
      return 'claude'; // Claude is great for design
    }
    if (prompt.includes('complex') || prompt.includes('logic') || prompt.includes('function') || prompt.includes('algorithm')) {
      return 'openai'; // GPT-4 for complex logic
    }
    if (prompt.includes('fast') || prompt.includes('simple') || prompt.includes('quick')) {
      return 'gemini'; // Gemini for speed
    }
    return aiProvider; // Default to selected
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');

    if (autoMode) {
      // Use Auto Mode
      setMessages(prev => [...prev, { role: 'user', content: userMessage, id: Date.now() }]);
      await runAutoMode(userMessage);
    } else {
      // Normal single message mode
      setLoading(true);
      setMessages(prev => [...prev, { role: 'user', content: userMessage, id: Date.now() }]);

      try {
        const response = await chatAPI.sendMessage(projectId, userMessage, aiProvider);
        setMessages(prev => [...prev, { role: 'assistant', content: response.data.message, id: response.data.message_id }]);
        setGeneratedCode(response.data.message);
        setGenerationsUsed(response.data.generations_used);
        setGenerationsLimit(response.data.generations_limit);
      } catch (error) {
        const errorMsg = error.response?.data?.detail || 'Something went wrong';
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${errorMsg}`, id: Date.now() }]);
      } finally {
        setLoading(false);
      }
    }
  };

  const extractCodeFromResponse = (text) => {
    if (!text) return '';
    const codeBlockRegex = /```(?:html|jsx|javascript|css)?\n([\s\S]*?)```/g;
    const matches = [];
    let match;
    while ((match = codeBlockRegex.exec(text)) !== null) matches.push(match[1]);
    return matches.join('\n\n');
  };

  const getPreviewContent = () => {
    const code = extractCodeFromResponse(generatedCode);
    if (!code) return '';
    return `<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><script src="https://cdn.tailwindcss.com"></script><style>* { margin: 0; padding: 0; box-sizing: border-box; } body { font-family: system-ui, -apple-system, sans-serif; }</style></head><body>${code}</body></html>`;
  };

  useEffect(() => {
    fetchProject();
    fetchChatHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  useEffect(() => {
    if (templatePrompt && project && messages.length === 0 && !loading) {
      setInput(templatePrompt);
      window.history.replaceState({}, '', `/builder/${projectId}`);
    }
  }, [templatePrompt, project, messages, loading, projectId]);

  const downloadCode = () => {
    const code = getPreviewContent();
    const blob = new Blob([code], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${project?.name || 'app'}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  // GitHub Deploy
  const deployToGitHub = async () => {
    if (!githubConnected) {
      navigate('/integrations');
      return;
    }
    
    setShowDeployModal(true);
    setDeployLoading(true);
    setDeployStatus({ step: 'Creating repository...', progress: 20 });
    
    try {
      const response = await integrationsAPI.deployToGitHub(projectId);
      setDeployStatus({
        step: 'Deployed!',
        progress: 100,
        success: true,
        data: response.data
      });
    } catch (error) {
      setDeployStatus({
        step: 'Failed',
        progress: 0,
        error: error.response?.data?.detail || 'Deployment failed'
      });
    } finally {
      setDeployLoading(false);
    }
  };

  if (projectLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="w-10 h-10 border-2 border-gray-200 border-t-gray-900 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-200 px-4 py-3 flex items-center justify-between bg-white">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/dashboard')} className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600" data-testid="back-to-dashboard">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="font-semibold text-gray-900" data-testid="project-name">{project?.name}</h1>
            <p className="text-xs text-gray-500">Generations: {generationsUsed}/{generationsLimit === -1 ? '∞' : generationsLimit}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Build with SSE Button */}
          <button
            onClick={() => navigate(`/build/${projectId}`)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-all shadow-sm flex items-center gap-2"
            data-testid="build-sse-btn"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Build
          </button>
          
          {/* Auto Mode Toggle */}
          <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg">
            <span className={`text-sm font-medium ${autoMode ? 'text-violet-600' : 'text-gray-500'}`}>Auto Mode</span>
            <button
              onClick={() => setAutoMode(!autoMode)}
              className={`relative w-11 h-6 rounded-full transition-colors ${autoMode ? 'bg-violet-600' : 'bg-gray-300'}`}
              disabled={isAutoRunning}
            >
              <span className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform shadow-sm ${autoMode ? 'left-6' : 'left-1'}`} />
            </button>
          </div>
          
          <select value={aiProvider} onChange={(e) => setAiProvider(e.target.value)} className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-200 text-gray-900" data-testid="ai-provider-select" disabled={isAutoRunning}>
            <optgroup label="🇺🇸 US/Global">
              <option value="openai">OpenAI GPT-5</option>
              <option value="gemini">Google Gemini</option>
              <option value="claude">Anthropic Claude</option>
              <option value="grok">xAI Grok</option>
              <option value="mistral">Mistral AI</option>
              <option value="cohere">Cohere</option>
              <option value="groq">Groq (Ultra Fast)</option>
              <option value="together">Together AI</option>
              <option value="perplexity">Perplexity</option>
              <option value="fireworks">Fireworks AI</option>
              <option value="ai21">AI21 Jamba</option>
            </optgroup>
            <optgroup label="🇨🇳 Chinese AI">
              <option value="deepseek">DeepSeek</option>
              <option value="qwen">Alibaba Qwen</option>
              <option value="moonshot">Moonshot Kimi</option>
              <option value="yi">01.AI Yi</option>
              <option value="zhipu">Zhipu GLM</option>
            </optgroup>
            <optgroup label="🤗 Open Source">
              <option value="huggingface">Hugging Face</option>
            </optgroup>
          </select>
          <button onClick={downloadCode} className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 transition-all shadow-sm" data-testid="download-code-btn">
            Download
          </button>
          <button 
            onClick={deployToGitHub}
            className="px-4 py-2 bg-gradient-to-r from-gray-800 to-gray-900 text-white rounded-lg text-sm font-medium hover:from-gray-700 hover:to-gray-800 transition-all shadow-sm flex items-center gap-2"
            data-testid="deploy-github-btn"
          >
            <span>🐙</span>
            {githubConnected ? 'Deploy' : 'Connect GitHub'}
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Chat Panel */}
        <div className="w-[420px] border-r border-gray-200 flex flex-col bg-gray-50">
          {/* Auto Mode Progress */}
          {isAutoRunning && autoSteps.length > 0 && (
            <div className="p-4 border-b border-gray-200 bg-violet-50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-violet-900">Auto Mode Running</span>
                <span className="text-xs text-violet-600">{currentStep}/{autoSteps.length}</span>
              </div>
              <div className="w-full h-2 bg-violet-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-violet-600 transition-all duration-500"
                  style={{ width: `${(currentStep / autoSteps.length) * 100}%` }}
                />
              </div>
              <p className="text-xs text-violet-700 mt-2">
                {autoSteps[currentStep - 1]?.title || 'Planning...'}
              </p>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4" data-testid="chat-messages">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-2xl flex items-center justify-center">
                  <span className="text-3xl">💬</span>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Start Building</h3>
                <p className="text-sm text-gray-500 mb-4">Describe what you want to create</p>
                {autoMode && (
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-violet-100 text-violet-700 rounded-full text-xs font-medium">
                    <span className="w-2 h-2 bg-violet-500 rounded-full animate-pulse"></span>
                    Auto Mode: AI will plan & build automatically
                  </div>
                )}
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={msg.id || i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user' 
                    ? 'bg-gray-900 text-white' 
                    : msg.role === 'system'
                    ? 'bg-violet-100 text-violet-800 border border-violet-200'
                    : 'bg-white border border-gray-200 shadow-sm'
                }`}>
                  {msg.role === 'assistant' ? (
                    <pre className="whitespace-pre-wrap text-sm overflow-x-auto text-gray-800">{msg.content}</pre>
                  ) : (
                    <p className="text-sm">{msg.content}</p>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></div>
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Form */}
          <form onSubmit={sendMessage} className="p-4 border-t border-gray-200 bg-white">
            <div className="flex gap-2">
              <input 
                type="text" 
                value={input} 
                onChange={(e) => setInput(e.target.value)} 
                placeholder={autoMode ? "Describe your full app idea..." : "Describe what you want to build..."} 
                className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-gray-300" 
                disabled={loading || isAutoRunning} 
                data-testid="chat-input" 
              />
              <button 
                type="submit" 
                disabled={loading || isAutoRunning || !input.trim()} 
                className={`px-4 py-3 rounded-xl font-medium transition-all disabled:opacity-50 ${
                  autoMode 
                    ? 'bg-violet-600 text-white hover:bg-violet-700' 
                    : 'bg-gray-900 text-white hover:bg-gray-800'
                }`}
                data-testid="send-message-btn"
              >
                {autoMode ? '🚀' : '→'}
              </button>
            </div>
            {autoMode && (
              <p className="text-xs text-violet-600 mt-2 text-center">
                Auto Mode will analyze, plan, and build your app step by step
              </p>
            )}
          </form>
        </div>

        {/* Preview Panel */}
        <div className="flex-1 flex flex-col bg-gray-50">
          <div className="flex border-b border-gray-200 bg-white">
            <button onClick={() => setActiveTab('preview')} className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'preview' ? 'border-gray-900 text-gray-900' : 'border-transparent text-gray-500 hover:text-gray-900'}`} data-testid="preview-tab">Preview</button>
            <button onClick={() => setActiveTab('code')} className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'code' ? 'border-gray-900 text-gray-900' : 'border-transparent text-gray-500 hover:text-gray-900'}`} data-testid="code-tab">Code</button>
          </div>

          <div className="flex-1 overflow-hidden">
            {activeTab === 'preview' ? (
              <div className="h-full bg-white">
                {generatedCode ? (
                  <iframe srcDoc={getPreviewContent()} title="Preview" className="w-full h-full border-0" sandbox="allow-scripts" data-testid="preview-iframe" />
                ) : (
                  <div className="h-full flex items-center justify-center bg-gray-50 text-gray-400">
                    <div className="text-center">
                      <div className="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-2xl flex items-center justify-center">
                        <span className="text-4xl">👁️</span>
                      </div>
                      <p className="text-gray-500">Preview will appear here</p>
                      <p className="text-sm text-gray-400 mt-1">Start chatting to generate your app</p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full overflow-auto bg-gray-900 p-4">
                <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap" data-testid="code-view">{extractCodeFromResponse(generatedCode) || 'No code generated yet'}</pre>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Deploy Modal */}
      {showDeployModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                🐙 Deploy to GitHub
              </h2>
              <button
                onClick={() => setShowDeployModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-all"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              {/* Progress */}
              {deployLoading && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">{deployStatus?.step}</span>
                    <span className="text-sm text-gray-500">{deployStatus?.progress}%</span>
                  </div>
                  <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-green-500 transition-all duration-300"
                      style={{ width: `${deployStatus?.progress}%` }}
                    />
                  </div>
                </div>
              )}
              
              {/* Success */}
              {deployStatus?.success && (
                <div className="text-center py-4">
                  <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-3xl">✅</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Deployed Successfully!</h3>
                  <p className="text-sm text-gray-500 mb-4">Your website is now live</p>
                  
                  {deployStatus.data?.pages_url && (
                    <a
                      href={deployStatus.data.pages_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-all"
                    >
                      🌐 View Live Site
                    </a>
                  )}
                  
                  {deployStatus.data?.repo_url && (
                    <a
                      href={deployStatus.data.repo_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block mt-3 text-sm text-blue-600 hover:underline"
                    >
                      View on GitHub →
                    </a>
                  )}
                </div>
              )}
              
              {/* Error */}
              {deployStatus?.error && (
                <div className="text-center py-4">
                  <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
                    <span className="text-3xl">❌</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Deployment Failed</h3>
                  <p className="text-sm text-red-600">{deployStatus.error}</p>
                  <button
                    onClick={() => {
                      setShowDeployModal(false);
                      setDeployStatus(null);
                    }}
                    className="mt-4 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-all"
                  >
                    Close
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Builder;
