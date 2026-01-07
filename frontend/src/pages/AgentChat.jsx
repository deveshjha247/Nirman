import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';

// Icons
const SendIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

const StopIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
  </svg>
);

const CodeIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
  </svg>
);

const PreviewIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
);

const CopyIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
  </svg>
);

const AgentIcon = ({ type }) => {
  const icons = {
    coder: '💻',
    browser: '🌐',
    file: '📁',
    planner: '📋',
    casual: '💬',
    mcp: '🔧'
  };
  return <span className="text-lg">{icons[type] || '🤖'}</span>;
};

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const AgentChat = () => {
  const { user, token } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [events, setEvents] = useState([]);
  const [showTimeline, setShowTimeline] = useState(true);
  const [showPreview, setShowPreview] = useState(false);
  const [activeCodeBlock, setActiveCodeBlock] = useState(null);
  const [copied, setCopied] = useState(false);
  
  const messagesEndRef = useRef(null);
  const eventSourceRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, events, scrollToBottom]);

  // Cleanup SSE on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // Send message
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setEvents([]);
    setCurrentJob(null);

    try {
      const response = await fetch(`${API_BASE}/agent/chat?message=${encodeURIComponent(input)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('Failed to send message');

      const data = await response.json();
      setCurrentJob(data);

      // Connect to SSE stream
      connectToStream(data.job_id);

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date().toISOString()
      }]);
      setIsLoading(false);
    }
  };

  // Connect to SSE stream
  const connectToStream = (jobId) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(`${API_BASE}/jobs/${jobId}/stream?token=${token}`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'stream_end') {
        eventSource.close();
        fetchJobResult(jobId);
        return;
      }

      setEvents(prev => [...prev, data]);

      // Update progress in current job
      if (data.progress !== undefined) {
        setCurrentJob(prev => prev ? { ...prev, progress: data.progress } : prev);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      eventSource.close();
      fetchJobResult(jobId);
    };
  };

  // Fetch job result
  const fetchJobResult = async (jobId) => {
    try {
      const response = await fetch(`${API_BASE}/jobs/${jobId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const job = await response.json();
        
        const assistantMessage = {
          id: Date.now(),
          role: 'assistant',
          content: job.response || 'Task completed.',
          timestamp: new Date().toISOString(),
          agent: job.current_agent,
          codeBlocks: job.code_blocks || [],
          hasPreview: job.has_preview,
          previewUrl: job.preview_url,
          jobId: job.id
        };

        setMessages(prev => [...prev, assistantMessage]);
        setCurrentJob(job);
        
        if (job.code_blocks?.length > 0) {
          setActiveCodeBlock(job.code_blocks[0]);
        }
      }
    } catch (error) {
      console.error('Error fetching job:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Stop job
  const stopJob = async () => {
    if (!currentJob?.job_id) return;

    try {
      await fetch(`${API_BASE}/jobs/${currentJob.job_id}/stop`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (error) {
      console.error('Error stopping job:', error);
    }
  };

  // Copy code
  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Get event icon and color
  const getEventStyle = (type) => {
    const styles = {
      job_started: { icon: '🚀', color: 'text-blue-400' },
      job_completed: { icon: '✅', color: 'text-green-400' },
      job_failed: { icon: '❌', color: 'text-red-400' },
      agent_selected: { icon: '🤖', color: 'text-purple-400' },
      agent_thinking: { icon: '🧠', color: 'text-yellow-400' },
      codegen_started: { icon: '💻', color: 'text-cyan-400' },
      codegen_progress: { icon: '⚙️', color: 'text-cyan-400' },
      codegen_done: { icon: '✨', color: 'text-cyan-400' },
      file_created: { icon: '📄', color: 'text-green-400' },
      preview_ready: { icon: '👁️', color: 'text-purple-400' },
      error: { icon: '⚠️', color: 'text-red-400' },
      info: { icon: 'ℹ️', color: 'text-gray-400' }
    };
    return styles[type] || { icon: '•', color: 'text-gray-400' };
  };

  // Render code block
  const renderCodeBlock = (block) => (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <CodeIcon />
          <span className="text-sm font-medium text-gray-300">{block.filename}</span>
          <span className="text-xs px-2 py-0.5 bg-gray-700 rounded text-gray-400">{block.language}</span>
        </div>
        <button
          onClick={() => copyCode(block.code)}
          className="p-1.5 hover:bg-gray-700 rounded transition-colors"
          title="Copy code"
        >
          {copied ? '✓' : <CopyIcon />}
        </button>
      </div>
      <pre className="p-4 text-sm overflow-x-auto">
        <code className="text-gray-300">{block.code}</code>
      </pre>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex">
      <Sidebar active="agent" />
      
      <main className="flex-1 flex">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="p-4 border-b border-gray-700 bg-gray-800/50 backdrop-blur">
            <div className="flex items-center justify-between max-w-4xl mx-auto">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                  <span className="text-xl">🤖</span>
                </div>
                <div>
                  <h1 className="text-lg font-semibold text-white">Nirman AI Agent</h1>
                  <p className="text-xs text-gray-400">AI Assistant • Ask anything</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowTimeline(!showTimeline)}
                  className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
                    showTimeline 
                      ? 'bg-violet-600 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Timeline
                </button>
              </div>
            </div>
          </header>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.length === 0 ? (
                <div className="text-center py-20">
                  <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-violet-500/20 to-purple-600/20 flex items-center justify-center">
                    <span className="text-4xl">🤖</span>
                  </div>
                  <h2 className="text-2xl font-bold text-white mb-2">Start a Conversation</h2>
                  <p className="text-gray-400 mb-8 max-w-md mx-auto">
                    I can help you write code, search the web, manage files, and more. 
                    Just type your request below.
                  </p>
                  
                  {/* Quick Actions */}
                  <div className="flex flex-wrap justify-center gap-3">
                    {[
                      { icon: '💻', text: 'Build a website', query: 'Create a modern landing page with HTML, CSS, and JavaScript' },
                      { icon: '🔍', text: 'Search the web', query: 'Search for latest AI news' },
                      { icon: '📋', text: 'Plan a project', query: 'Plan a full-stack web application' },
                      { icon: '🔧', text: 'Use MCP tools', query: 'Use MCP to check the weather' }
                    ].map((action, i) => (
                      <button
                        key={i}
                        onClick={() => setInput(action.query)}
                        className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-300 flex items-center gap-2 transition-colors"
                      >
                        <span>{action.icon}</span>
                        {action.text}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-3xl ${msg.role === 'user' ? 'order-2' : ''}`}>
                      {/* Avatar */}
                      <div className={`flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          msg.role === 'user' 
                            ? 'bg-gradient-to-br from-blue-500 to-cyan-500' 
                            : 'bg-gradient-to-br from-violet-500 to-purple-600'
                        }`}>
                          {msg.role === 'user' ? '👤' : msg.agent ? <AgentIcon type={msg.agent} /> : '🤖'}
                        </div>
                        
                        <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                          {msg.agent && (
                            <span className="text-xs text-gray-500 mb-1 capitalize">{msg.agent} Agent</span>
                          )}
                          
                          <div className={`p-4 rounded-2xl ${
                            msg.role === 'user'
                              ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white'
                              : 'bg-gray-800 text-gray-100'
                          }`}>
                            <p className="whitespace-pre-wrap">{msg.content}</p>
                          </div>

                          {/* Code Blocks */}
                          {msg.codeBlocks?.length > 0 && (
                            <div className="mt-4 w-full space-y-3">
                              {msg.codeBlocks.map((block, i) => (
                                <div key={i}>
                                  {renderCodeBlock(block)}
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Preview Button */}
                          {msg.hasPreview && (
                            <button
                              onClick={() => setShowPreview(true)}
                              className="mt-3 px-4 py-2 bg-violet-600 hover:bg-violet-700 rounded-lg text-sm text-white flex items-center gap-2 transition-colors"
                            >
                              <PreviewIcon />
                              View Preview
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}

              {/* Loading State */}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center animate-pulse">
                      🤖
                    </div>
                    <div className="bg-gray-800 rounded-2xl p-4">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-gray-700 bg-gray-800/50 backdrop-blur">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-end gap-3">
                <div className="flex-1 relative">
                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                      }
                    }}
                    placeholder="Type your message... (Shift+Enter for new line)"
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none"
                    rows={1}
                    style={{ minHeight: '48px', maxHeight: '200px' }}
                  />
                </div>
                
                <button
                  onClick={isLoading ? stopJob : sendMessage}
                  disabled={!input.trim() && !isLoading}
                  className={`p-3 rounded-xl transition-all ${
                    isLoading
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : input.trim()
                        ? 'bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white'
                        : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  {isLoading ? <StopIcon /> : <SendIcon />}
                </button>
              </div>
              
              {/* Progress Bar */}
              {isLoading && currentJob?.progress > 0 && (
                <div className="mt-3">
                  <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-violet-500 to-purple-500 transition-all duration-300"
                      style={{ width: `${currentJob.progress}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1 text-center">{currentJob.progress}% complete</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Timeline Sidebar */}
        {showTimeline && events.length > 0 && (
          <div className="w-80 border-l border-gray-700 bg-gray-800/30 overflow-y-auto">
            <div className="p-4 border-b border-gray-700 sticky top-0 bg-gray-800/90 backdrop-blur">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <span>📊</span> Build Timeline
              </h3>
            </div>
            
            <div className="p-4 space-y-3">
              {events.map((event, i) => {
                const style = getEventStyle(event.type);
                return (
                  <div key={i} className="flex items-start gap-3">
                    <div className={`flex-shrink-0 ${style.color}`}>
                      {style.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-300 break-words">{event.message}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {new Date(event.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                    {event.progress !== undefined && (
                      <span className="text-xs text-gray-500">{event.progress}%</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </main>

      {/* Preview Modal */}
      {showPreview && currentJob?.has_preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="bg-gray-900 rounded-xl w-full max-w-5xl h-[80vh] flex flex-col mx-4">
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <PreviewIcon />
                Live Preview
              </h3>
              <button
                onClick={() => setShowPreview(false)}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 bg-white">
              <iframe
                src={`${API_BASE}/preview/${currentJob.id || currentJob.job_id}`}
                className="w-full h-full border-0"
                title="Preview"
                sandbox="allow-scripts"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentChat;
