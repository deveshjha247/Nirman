import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { projectsAPI, templatesAPI } from '../lib/api';
import Sidebar from '../components/Sidebar';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [loading, setLoading] = useState(true);
  const [promptInput, setPromptInput] = useState('');

  useEffect(() => {
    fetchProjects();
    fetchTemplates();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await projectsAPI.getProjects();
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await templatesAPI.getTemplates();
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const createProject = async (e) => {
    e.preventDefault();
    try {
      const response = await projectsAPI.createProject(newProjectName, newProjectDesc, 'react');
      setProjects([response.data, ...projects]);
      setShowNewProject(false);
      setNewProjectName('');
      setNewProjectDesc('');
      navigate(`/builder/${response.data.id}`);
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to create project');
    }
  };

  const handleQuickCreate = async (e) => {
    e.preventDefault();
    if (!promptInput.trim()) return;
    try {
      const response = await projectsAPI.createProject('New Project', promptInput, 'react');
      navigate(`/builder/${response.data.id}?prompt=${encodeURIComponent(promptInput)}`);
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to create project');
    }
  };

  const deleteProject = async (projectId) => {
    if (!window.confirm('Are you sure you want to delete this project?')) return;
    try {
      await projectsAPI.deleteProject(projectId);
      setProjects(projects.filter(p => p.id !== projectId));
    } catch (error) {
      console.error('Failed to delete project:', error);
    }
  };

  const createFromTemplate = async (template) => {
    try {
      const response = await projectsAPI.createProject(template.name, template.description, 'react');
      navigate(`/builder/${response.data.id}?prompt=${encodeURIComponent(template.prompt)}`);
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to create project');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50/30 via-white to-purple-50/30 flex">
      <Sidebar active="projects" />
      
      <main className="flex-1 overflow-auto">
        {/* Hero Section with Prompt Input */}
        <div className="relative bg-gradient-to-b from-white to-purple-50/20 border-b border-purple-100/50">
          <div className="max-w-4xl mx-auto px-8 py-20">
            <div className="text-center mb-12">
              <h1 className="text-5xl font-bold text-gray-900 mb-4">
                What can I build for you?
              </h1>
              <p className="text-gray-600 text-xl">
                Describe your idea and let AI create it for you
              </p>
            </div>
            
            {/* Quick Create Prompt Input */}
            <form onSubmit={handleQuickCreate} className="relative">
              <div className="relative group">
                <input
                  type="text"
                  value={promptInput}
                  onChange={(e) => setPromptInput(e.target.value)}
                  placeholder="Build a landing page for my SaaS product..."
                  className="w-full px-7 py-6 bg-white/90 backdrop-blur-sm border border-purple-100 rounded-2xl text-gray-900 text-lg placeholder-gray-400 shadow-2xl shadow-purple-100/20 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 focus:shadow-2xl transition-all duration-300 pr-36 group-hover:border-purple-200 group-hover:shadow-purple-200/30"
                  data-testid="quick-create-input"
                />
                <button
                  type="submit"
                  className="absolute right-3 top-1/2 -translate-y-1/2 px-7 py-3 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-violet-700 transition-all duration-200 shadow-lg shadow-purple-300/50 hover:shadow-xl hover:scale-105 active:scale-95"
                  data-testid="quick-create-btn"
                >
                  Create
                </button>
              </div>
            </form>

            {/* Quick Action Chips */}
            <div className="flex flex-wrap justify-center gap-3 mt-8">
              {['Create slides', 'Build website', 'Develop apps', 'Design', 'More'].map((action, i) => (
                <button
                  key={i}
                  onClick={() => setPromptInput(action === 'More' ? '' : `${action} for my project`)}
                  className="px-5 py-2.5 bg-white/90 backdrop-blur-sm border border-purple-100 hover:border-purple-200 hover:shadow-xl hover:shadow-purple-100/20 hover:-translate-y-0.5 text-gray-700 hover:text-purple-700 rounded-full text-sm font-medium transition-all duration-200 shadow-lg shadow-gray-100/50"
                >
                  {action}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="max-w-6xl mx-auto px-8 py-12">
          {/* Stats Row */}
          <div className="flex items-center gap-6 mb-12">
            <div className="flex items-center gap-4 px-6 py-4 bg-white/90 backdrop-blur-sm border border-purple-100 rounded-xl shadow-lg shadow-purple-100/20">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-100 to-violet-100 flex items-center justify-center">
                <span className="text-purple-600 text-2xl">⚡</span>
              </div>
              <div>
                <p className="text-sm text-gray-500 font-medium">Generations</p>
                <p className="text-xl font-bold text-gray-900">
                  {user?.generations_used || 0} / {user?.generations_limit === -1 ? '∞' : user?.generations_limit}
                </p>
              </div>
            </div>
            <button 
              onClick={() => setShowNewProject(true)} 
              className="ml-auto px-7 py-4 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-violet-700 transition-all duration-200 shadow-lg shadow-purple-300/50 hover:shadow-xl hover:scale-105 flex items-center gap-2.5" 
              data-testid="new-project-btn"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
              </svg>
              New Project
            </button>
          </div>

          {/* Templates Section */}
          <div className="mb-16">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold text-gray-900">Start from Template</h2>
              <span className="text-sm text-purple-600 font-medium">{templates.length} templates</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-5">
              {templates.map((template) => (
                <button 
                  key={template.id} 
                  onClick={() => createFromTemplate(template)} 
                  className="p-6 bg-white/90 backdrop-blur-sm border border-purple-100 rounded-2xl hover:border-purple-200 hover:shadow-2xl hover:shadow-purple-100/20 hover:-translate-y-1 transition-all duration-300 text-left group" 
                  data-testid={`template-${template.id}`}
                >
                  <span className="text-4xl block mb-4 group-hover:scale-125 transition-transform duration-300">{template.icon}</span>
                  <span className="font-semibold text-sm text-gray-900">{template.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Projects Section */}
          <div>
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold text-gray-900">Your Projects</h2>
              <span className="text-sm text-purple-600 font-medium">{projects.length} projects</span>
            </div>
            
            {loading ? (
              <div className="flex items-center justify-center py-20">
                <div className="w-12 h-12 border-3 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
              </div>
            ) : projects.length === 0 ? (
              <div className="text-center py-24 bg-white/90 backdrop-blur-sm border border-purple-100 rounded-3xl shadow-xl shadow-purple-100/20">
                <div className="w-20 h-20 mx-auto mb-8 bg-gradient-to-br from-purple-100 to-violet-100 rounded-2xl flex items-center justify-center">
                  <span className="text-5xl">📁</span>
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">No projects yet</h3>
                <p className="text-gray-600 mb-10 max-w-md mx-auto text-lg">Create your first project or start from a template above</p>
                <button 
                  onClick={() => setShowNewProject(true)} 
                  className="px-8 py-4 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-violet-700 transition-all duration-200 shadow-lg shadow-purple-300/50 hover:shadow-xl hover:scale-105"
                >
                  Create Project
                </button>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                {projects.map((project) => (
                  <div 
                    key={project.id} 
                    className="bg-white/90 backdrop-blur-sm border border-purple-100 rounded-2xl overflow-hidden hover:border-purple-200 hover:shadow-2xl hover:shadow-purple-100/20 hover:-translate-y-1 transition-all duration-300 group" 
                    data-testid={`project-card-${project.id}`}
                  >
                    <div className="aspect-video bg-gradient-to-br from-purple-50 via-violet-50 to-fuchsia-50 flex items-center justify-center border-b border-purple-100">
                      <span className="text-6xl opacity-70 group-hover:scale-125 transition-transform duration-300">💻</span>
                    </div>
                    <div className="p-6">
                      <h3 className="font-bold text-gray-900 mb-2.5 text-lg">{project.name}</h3>
                      <p className="text-sm text-gray-600 mb-5 line-clamp-2 leading-relaxed">{project.description || 'No description'}</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-400 flex items-center gap-1.5 font-medium">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {new Date(project.updated_at).toLocaleDateString()}
                        </span>
                        <div className="flex gap-2">
                          <button 
                            onClick={() => navigate(`/builder/${project.id}`)} 
                            className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-lg text-sm font-semibold hover:from-purple-700 hover:to-violet-700 transition-all duration-200 shadow-lg shadow-purple-300/50 hover:scale-105" 
                            data-testid={`open-project-${project.id}`}
                          >
                            Open
                          </button>
                          <button 
                            onClick={() => deleteProject(project.id)} 
                            className="px-5 py-2.5 bg-red-50 text-red-600 rounded-lg text-sm font-semibold hover:bg-red-100 transition-all duration-200" 
                            data-testid={`delete-project-${project.id}`}
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* New Project Modal */}
      {showNewProject && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-md flex items-center justify-center z-50 p-6">
          <div className="bg-white/95 backdrop-blur-xl border border-purple-100 rounded-3xl w-full max-w-md p-8 shadow-2xl shadow-purple-200/30 animate-slide-up" data-testid="new-project-modal">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold text-gray-900">Create New Project</h2>
              <button 
                onClick={() => setShowNewProject(false)}
                className="w-9 h-9 rounded-full bg-gray-100 hover:bg-purple-50 hover:text-purple-600 flex items-center justify-center transition-all"
              >
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <form onSubmit={createProject} className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2.5">Project Name</label>
                <input 
                  type="text" 
                  value={newProjectName} 
                  onChange={(e) => setNewProjectName(e.target.value)} 
                  className="w-full px-5 py-3.5 bg-gray-50 border border-purple-100 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 focus:bg-white transition-all" 
                  placeholder="My Awesome App" 
                  required 
                  data-testid="new-project-name-input" 
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2.5">Description (optional)</label>
                <textarea 
                  value={newProjectDesc} 
                  onChange={(e) => setNewProjectDesc(e.target.value)} 
                  className="w-full px-5 py-3.5 bg-gray-50 border border-purple-100 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 focus:bg-white transition-all resize-none" 
                  placeholder="What are you building?" 
                  rows={3} 
                  data-testid="new-project-desc-input" 
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button 
                  type="button" 
                  onClick={() => setShowNewProject(false)} 
                  className="flex-1 py-3.5 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-all duration-200" 
                  data-testid="cancel-new-project-btn"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="flex-1 py-3.5 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-violet-700 transition-all duration-200 shadow-lg shadow-purple-300/50 hover:shadow-xl hover:scale-105" 
                  data-testid="create-project-btn"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
