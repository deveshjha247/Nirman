import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Download, 
  ExternalLink, 
  Code2, 
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  FolderOpen,
  History,
  Eye
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import BuildChat from '../components/BuildChat';
import { projectsAPI, buildAPI, API_BASE } from '../lib/api';

// Status badge component
const StatusBadge = ({ status }) => {
  const config = {
    queued: { color: 'bg-gray-100 text-gray-700', icon: Clock },
    running: { color: 'bg-blue-100 text-blue-700', icon: Loader2, spin: true },
    success: { color: 'bg-green-100 text-green-700', icon: CheckCircle2 },
    failed: { color: 'bg-red-100 text-red-700', icon: XCircle },
    cancelled: { color: 'bg-orange-100 text-orange-700', icon: XCircle }
  };
  
  const { color, icon: Icon, spin } = config[status] || config.queued;
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${color}`}>
      <Icon className={`w-3 h-3 ${spin ? 'animate-spin' : ''}`} />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};

function Build() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showHistory, setShowHistory] = useState(false);
  const [previewCode, setPreviewCode] = useState('');
  const [showPreview, setShowPreview] = useState(false);

  // Load project and build history
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch project
        const projectRes = await projectsAPI.getProject(projectId);
        setProject(projectRes.data);
        setPreviewCode(projectRes.data.html_code || '');
        
        // Fetch build history
        const jobsRes = await buildAPI.listProjectJobs(projectId, 5);
        setJobs(jobsRes.data.jobs || []);
      } catch (err) {
        console.error('Failed to fetch data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (projectId) {
      fetchData();
    }
  }, [projectId]);

  // Handle build completion
  const handleBuildComplete = async (event) => {
    // Refresh project to get updated code
    try {
      const projectRes = await projectsAPI.getProject(projectId);
      setProject(projectRes.data);
      setPreviewCode(projectRes.data.html_code || '');
      
      // Refresh job history
      const jobsRes = await buildAPI.listProjectJobs(projectId, 5);
      setJobs(jobsRes.data.jobs || []);
    } catch (err) {
      console.error('Failed to refresh:', err);
    }
  };

  // Handle download
  const handleDownload = () => {
    if (!previewCode) return;
    
    const blob = new Blob([previewCode], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${project?.name || 'project'}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => navigate('/builder')}
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Back
            </Button>
            <div>
              <h1 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <FolderOpen className="w-5 h-5 text-purple-500" />
                {project?.name || 'Project'}
              </h1>
              <p className="text-sm text-gray-500">{project?.description || 'AI-powered build'}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowHistory(!showHistory)}
            >
              <History className="w-4 h-4 mr-1" />
              History
            </Button>
            {previewCode && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowPreview(!showPreview)}
                >
                  <Eye className="w-4 h-4 mr-1" />
                  Preview
                </Button>
                <Button
                  size="sm"
                  onClick={handleDownload}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Download className="w-4 h-4 mr-1" />
                  Download
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-[calc(100vh-120px)]">
          {/* Build Chat Panel */}
          <div className={`${showHistory || showPreview ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
            <Card className="h-full flex flex-col">
              <CardHeader className="border-b py-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Code2 className="w-5 h-5 text-purple-500" />
                  AI Build Agent
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 p-0 overflow-hidden">
                <BuildChat 
                  projectId={projectId}
                  onBuildComplete={handleBuildComplete}
                  className="h-full"
                />
              </CardContent>
            </Card>
          </div>

          {/* Side Panel - History or Preview */}
          {(showHistory || showPreview) && (
            <div className="lg:col-span-1">
              {showHistory && (
                <Card className="h-full overflow-hidden">
                  <CardHeader className="border-b py-3">
                    <CardTitle className="text-lg flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <History className="w-5 h-5 text-blue-500" />
                        Build History
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowHistory(false)}
                      >
                        <XCircle className="w-4 h-4" />
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0 overflow-y-auto max-h-[calc(100vh-220px)]">
                    {jobs.length === 0 ? (
                      <div className="p-4 text-center text-gray-400">
                        <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p>No build history yet</p>
                      </div>
                    ) : (
                      <div className="divide-y">
                        {jobs.map((job) => (
                          <div key={job.id} className="p-4 hover:bg-gray-50">
                            <div className="flex items-start justify-between">
                              <div className="min-w-0 flex-1">
                                <p className="text-sm font-medium text-gray-900 truncate">
                                  {job.prompt?.slice(0, 50)}...
                                </p>
                                <p className="text-xs text-gray-400 mt-1">
                                  {new Date(job.created_at).toLocaleString()}
                                </p>
                              </div>
                              <StatusBadge status={job.status} />
                            </div>
                            <div className="mt-2 flex items-center gap-2">
                              <span className="text-xs text-gray-500">
                                Progress: {job.progress}%
                              </span>
                              {job.ai_provider && (
                                <span className="text-xs px-2 py-0.5 bg-gray-100 rounded-full">
                                  {job.ai_provider}
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {showPreview && (
                <Card className="h-full overflow-hidden">
                  <CardHeader className="border-b py-3">
                    <CardTitle className="text-lg flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Eye className="w-5 h-5 text-green-500" />
                        Live Preview
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowPreview(false)}
                      >
                        <XCircle className="w-4 h-4" />
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0 h-[calc(100%-60px)]">
                    {previewCode ? (
                      <iframe
                        srcDoc={previewCode}
                        title="Preview"
                        className="w-full h-full border-0"
                        sandbox="allow-scripts allow-same-origin"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full text-gray-400">
                        <div className="text-center">
                          <Code2 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                          <p>No preview available</p>
                          <p className="text-xs mt-1">Start a build to generate code</p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Build;
