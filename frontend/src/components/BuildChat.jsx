import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Loader2, 
  CheckCircle2, 
  XCircle, 
  Zap, 
  Brain, 
  Code2, 
  Package, 
  Download,
  AlertCircle,
  Sparkles,
  Bot,
  Clock
} from 'lucide-react';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { buildAPI, API_BASE } from '../lib/api';

// Event type icons and colors
const EVENT_CONFIG = {
  job_started: { icon: Sparkles, color: 'text-purple-500', bg: 'bg-purple-50' },
  planning_started: { icon: Brain, color: 'text-blue-500', bg: 'bg-blue-50' },
  planning_done: { icon: CheckCircle2, color: 'text-blue-600', bg: 'bg-blue-50' },
  codegen_started: { icon: Code2, color: 'text-amber-500', bg: 'bg-amber-50' },
  codegen_progress: { icon: Loader2, color: 'text-amber-500', bg: 'bg-amber-50', spin: true },
  codegen_done: { icon: CheckCircle2, color: 'text-amber-600', bg: 'bg-amber-50' },
  packaging: { icon: Package, color: 'text-indigo-500', bg: 'bg-indigo-50' },
  artifact_ready: { icon: Download, color: 'text-green-500', bg: 'bg-green-50' },
  error: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50' },
  job_completed: { icon: CheckCircle2, color: 'text-green-600', bg: 'bg-green-50' }
};

// AI Provider badges
const PROVIDER_BADGES = {
  openai: { name: 'GPT-4o', color: 'bg-green-100 text-green-800' },
  gemini: { name: 'Gemini 2.0', color: 'bg-blue-100 text-blue-800' },
  claude: { name: 'Claude Sonnet', color: 'bg-purple-100 text-purple-800' },
  auto: { name: 'Auto', color: 'bg-gray-100 text-gray-800' }
};

function BuildChat({ 
  projectId, 
  onBuildComplete,
  initialPrompt = '',
  className = ''
}) {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [aiProvider, setAiProvider] = useState('auto');
  const [isBuilding, setIsBuilding] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [events, setEvents] = useState([]);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  
  const eventSourceRef = useRef(null);
  const eventsEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to latest event
  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  // Cleanup EventSource on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // Connect to SSE stream
  const connectToStream = useCallback((jobId) => {
    // Get token from localStorage
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Authentication required');
      return;
    }

    const streamUrl = `${API_BASE}/jobs/${jobId}/stream?token=${token}`;
    
    const eventSource = new EventSource(streamUrl);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Check for stream end
        if (data.type === 'stream_end') {
          eventSource.close();
          setIsBuilding(false);
          return;
        }

        // Add event to timeline
        setEvents(prev => {
          // Avoid duplicates
          const exists = prev.some(e => e.id === data.id);
          if (exists) return prev;
          return [...prev, data];
        });

        // Update progress from payload
        if (data.payload?.progress) {
          setProgress(data.payload.progress);
        }

        // Handle specific events
        if (data.type === 'job_completed') {
          setIsBuilding(false);
          if (onBuildComplete) {
            onBuildComplete(data);
          }
        } else if (data.type === 'error') {
          setError(data.message);
          setIsBuilding(false);
        }
      } catch (e) {
        console.error('Error parsing SSE event:', e);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE Error:', err);
      eventSource.close();
      setIsBuilding(false);
      setError('Connection lost. Please try again.');
    };
  }, [onBuildComplete]);

  // Start build
  const handleStartBuild = async () => {
    if (!prompt.trim() || !projectId) return;

    setIsBuilding(true);
    setEvents([]);
    setProgress(0);
    setError(null);

    try {
      const response = await buildAPI.startBuild(projectId, prompt.trim(), aiProvider);
      const { id: jobId } = response.data;
      
      setCurrentJob({ id: jobId, status: 'queued' });
      
      // Connect to SSE stream
      connectToStream(jobId);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start build');
      setIsBuilding(false);
    }
  };

  // Cancel build
  const handleCancel = async () => {
    if (!currentJob?.id) return;

    try {
      await buildAPI.cancelJob(currentJob.id);
      eventSourceRef.current?.close();
      setIsBuilding(false);
    } catch (err) {
      console.error('Failed to cancel:', err);
    }
  };

  // Render event item
  const renderEvent = (event, index) => {
    const config = EVENT_CONFIG[event.type] || EVENT_CONFIG.job_started;
    const Icon = config.icon;
    const providerBadge = event.payload?.provider ? PROVIDER_BADGES[event.payload.provider] : null;

    return (
      <div 
        key={event.id || index}
        className={`flex items-start gap-3 p-3 rounded-lg ${config.bg} animate-fadeIn`}
      >
        <div className={`mt-0.5 ${config.color}`}>
          <Icon className={`w-5 h-5 ${config.spin ? 'animate-spin' : ''}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-medium text-gray-900">{event.message}</p>
            {providerBadge && (
              <span className={`text-xs px-2 py-0.5 rounded-full ${providerBadge.color}`}>
                {providerBadge.name}
              </span>
            )}
          </div>
          {event.payload?.preview && (
            <pre className="mt-2 text-xs text-gray-600 bg-white/50 p-2 rounded overflow-x-auto max-h-32">
              {event.payload.preview}
            </pre>
          )}
          {event.payload?.download_url && (
            <a 
              href={event.payload.download_url}
              className="mt-2 inline-flex items-center gap-1 text-sm text-green-600 hover:text-green-700"
            >
              <Download className="w-4 h-4" />
              Download Project
            </a>
          )}
          <p className="text-xs text-gray-400 mt-1">
            <Clock className="w-3 h-3 inline mr-1" />
            {new Date(event.created_at).toLocaleTimeString()}
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Events Timeline */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {events.length === 0 && !isBuilding && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <Bot className="w-16 h-16 mb-4 opacity-50" />
            <p className="text-lg font-medium">Ready to Build</p>
            <p className="text-sm">Enter a prompt below to start generating your app</p>
          </div>
        )}
        
        {events.map(renderEvent)}
        
        {/* Loading state */}
        {isBuilding && events.length === 0 && (
          <div className="flex items-center gap-3 p-4 bg-purple-50 rounded-lg">
            <Loader2 className="w-5 h-5 text-purple-500 animate-spin" />
            <p className="text-sm text-purple-700">Starting build...</p>
          </div>
        )}
        
        <div ref={eventsEndRef} />
      </div>

      {/* Progress Bar */}
      {isBuilding && (
        <div className="px-4 py-2 border-t bg-gray-50">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500">Progress</span>
            <span className="text-xs font-medium text-gray-700">{progress}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mx-4 mb-2 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-800">Build Error</p>
            <p className="text-xs text-red-600">{error}</p>
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="border-t bg-white p-4">
        {/* AI Provider Selector */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-gray-500">AI Provider:</span>
          <div className="flex gap-1">
            {Object.entries(PROVIDER_BADGES).map(([key, badge]) => (
              <button
                key={key}
                onClick={() => setAiProvider(key)}
                disabled={isBuilding}
                className={`text-xs px-2 py-1 rounded-full transition-colors ${
                  aiProvider === key 
                    ? badge.color + ' ring-2 ring-offset-1 ring-gray-400' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {badge.name}
              </button>
            ))}
          </div>
        </div>

        {/* Prompt Input */}
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe what you want to build... e.g., A modern portfolio website with dark mode"
            disabled={isBuilding}
            className="flex-1 min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:bg-gray-50 disabled:cursor-not-allowed"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.ctrlKey && !isBuilding) {
                handleStartBuild();
              }
            }}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between mt-3">
          <p className="text-xs text-gray-400">
            Press Ctrl+Enter to build
          </p>
          <div className="flex gap-2">
            {isBuilding ? (
              <Button 
                variant="destructive" 
                size="sm"
                onClick={handleCancel}
              >
                <XCircle className="w-4 h-4 mr-1" />
                Cancel
              </Button>
            ) : (
              <Button 
                onClick={handleStartBuild}
                disabled={!prompt.trim() || !projectId}
                className="bg-purple-600 hover:bg-purple-700"
              >
                <Zap className="w-4 h-4 mr-1" />
                Start Build
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default BuildChat;
