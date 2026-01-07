import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to requests
export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};

// Auth API
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (email, name, password, referral_code) => api.post('/auth/register', { email, name, password, referral_code }),
  getMe: () => api.get('/auth/me')
};

// Plans API
export const plansAPI = {
  getPlans: () => api.get('/plans'),
  purchase: (plan, billing_cycle, use_wallet, coupon_code) => 
    api.post('/plans/purchase', { plan, billing_cycle, use_wallet, coupon_code }),
  validateCoupon: (code, plan, amount) => 
    api.post(`/coupons/validate?code=${code}&plan=${plan}&amount=${amount}`)
};

// Wallet API
export const walletAPI = {
  getWallet: () => api.get('/wallet'),
  getTransactions: (type, limit, offset) => {
    const params = new URLSearchParams();
    if (type) params.append('type', type);
    if (limit) params.append('limit', limit);
    if (offset) params.append('offset', offset);
    return api.get(`/wallet/transactions?${params.toString()}`);
  },
  addMoney: (amount, paymentMethod = 'auto') => 
    api.post(`/wallet/add?payment_method=${paymentMethod}`, { amount }),
  verifyPayment: (order_id) => api.post('/wallet/verify-payment', { order_id }),
  verifyRazorpay: (orderId, paymentId, signature) => 
    api.post('/wallet/verify-razorpay', { 
      razorpay_order_id: orderId, 
      razorpay_payment_id: paymentId, 
      razorpay_signature: signature 
    }),
  verifyCashfree: (orderId) => api.post(`/wallet/verify-cashfree?order_id=${orderId}`),
  getPaymentMethods: () => api.get('/wallet/payment-methods'),
  withdraw: (amount, bankAccount, ifscCode, accountHolder, upiId) =>
    api.post('/wallet/withdraw', { 
      amount, 
      bank_account: bankAccount, 
      ifsc_code: ifscCode, 
      account_holder: accountHolder,
      upi_id: upiId
    }),
  getWithdrawals: () => api.get('/wallet/withdrawals')
};

// Referrals API
export const referralsAPI = {
  getReferrals: () => api.get('/referrals')
};

// Projects API
export const projectsAPI = {
  getProjects: () => api.get('/projects'),
  getProject: (id) => api.get(`/projects/${id}`),
  createProject: (name, description, framework) => 
    api.post('/projects', { name, description, framework }),
  updateProject: (id, data) => api.put(`/projects/${id}`, data),
  deleteProject: (id) => api.delete(`/projects/${id}`)
};

// Chat API
export const chatAPI = {
  sendMessage: (project_id, message, ai_provider) => 
    api.post('/chat', { project_id, message, ai_provider }),
  getHistory: (project_id) => api.get(`/chat/${project_id}`)
};

// Templates API
export const templatesAPI = {
  getTemplates: () => api.get('/templates')
};

// Admin API
export const adminAPI = {
  getStats: () => api.get('/admin/stats'),
  getUsers: (search = '') => api.get(`/admin/users${search ? `?search=${encodeURIComponent(search)}` : ''}`),
  getUserDetail: (userId) => api.get(`/admin/users/${userId}`),
  updateUser: (userId, data) => api.put(`/admin/users/${userId}`, data),
  banUser: (userId, reason) => api.post(`/admin/users/${userId}/ban?reason=${encodeURIComponent(reason || '')}`),
  unbanUser: (userId) => api.post(`/admin/users/${userId}/unban`),
  forceLogout: (userId) => api.post(`/admin/users/${userId}/force-logout`),
  resetPassword: (userId) => api.post(`/admin/users/${userId}/reset-password`),
  extendPlan: (userId, days) => api.post(`/admin/users/${userId}/extend-plan?days=${days}`),
  setLimits: (userId, params) => api.post(`/admin/users/${userId}/set-limits`, null, { params }),
  
  // Purchases
  getPurchases: (status) => api.get(`/admin/purchases${status ? `?status=${status}` : ''}`),
  refundPurchase: (purchaseId, reason) => api.post(`/admin/purchases/${purchaseId}/refund?reason=${encodeURIComponent(reason)}`),
  exportInvoices: (startDate, endDate) => api.get(`/admin/invoices/export${startDate ? `?start_date=${startDate}` : ''}${endDate ? `&end_date=${endDate}` : ''}`),
  
  // Errors
  getErrors: (errorType) => api.get(`/admin/errors${errorType ? `?error_type=${errorType}` : ''}`),
  
  // Coupons
  getCoupons: () => api.get('/admin/coupons'),
  createCoupon: (data) => api.post('/admin/coupons', data),
  updateCoupon: (id, data) => api.put(`/admin/coupons/${id}`, data),
  deleteCoupon: (id) => api.delete(`/admin/coupons/${id}`),
  
  // Plans
  getPlans: () => api.get('/admin/plans'),
  createPlan: (data) => api.post('/admin/plans', data),
  updatePlan: (id, data) => api.put(`/admin/plans/${id}`, data),
  deletePlan: (id) => api.delete(`/admin/plans/${id}`),
  initDefaultPlans: () => api.post('/admin/plans/init-defaults'),
  
  // AI Usage
  getAIUsage: (provider) => api.get(`/admin/ai-usage${provider ? `?provider=${provider}` : ''}`),
  getAIProviders: () => api.get('/admin/ai-providers'),
  updateAIProvider: (provider, data) => api.put(`/admin/ai-providers/${provider}`, null, { params: data }),
  
  // Support
  getSupportTickets: (status, category) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (category) params.append('category', category);
    return api.get(`/admin/support/tickets${params.toString() ? `?${params.toString()}` : ''}`);
  },
  getTicketDetail: (ticketId) => api.get(`/admin/support/tickets/${ticketId}`),
  replyTicket: (ticketId, message) => api.post(`/admin/support/tickets/${ticketId}/reply`, { message }),
  updateTicketStatus: (ticketId, status, resolution) => {
    const params = new URLSearchParams({ status });
    if (resolution) params.append('resolution', resolution);
    return api.put(`/admin/support/tickets/${ticketId}/status?${params.toString()}`);
  },
  assignTicket: (ticketId, adminId) => api.put(`/admin/support/tickets/${ticketId}/assign${adminId ? `?admin_id=${adminId}` : ''}`),
  getSupportStats: () => api.get('/admin/support/stats'),
  
  // Audit Logs
  getAuditLogs: (action, adminId) => {
    const params = new URLSearchParams();
    if (action) params.append('action', action);
    if (adminId) params.append('admin_id', adminId);
    return api.get(`/admin/audit-logs${params.toString() ? `?${params.toString()}` : ''}`);
  },
  
  // Projects Management
  getProjects: (plan, status) => {
    const params = new URLSearchParams();
    if (plan) params.append('plan', plan);
    if (status) params.append('status', status);
    return api.get(`/admin/projects${params.toString() ? `?${params.toString()}` : ''}`);
  },
  getProjectDetail: (projectId) => api.get(`/admin/projects/${projectId}`),
  freezeProject: (projectId, reason) => api.post(`/admin/projects/${projectId}/freeze${reason ? `?reason=${encodeURIComponent(reason)}` : ''}`),
  unfreezeProject: (projectId) => api.post(`/admin/projects/${projectId}/unfreeze`),
  deleteProject: (projectId) => api.delete(`/admin/projects/${projectId}`),
  restoreProject: (projectId) => api.post(`/admin/projects/${projectId}/restore`),
  regenerateProject: (projectId) => api.post(`/admin/projects/${projectId}/regenerate`),
  
  // Jobs Management
  getJobs: (status) => api.get(`/admin/jobs${status ? `?status=${status}` : ''}`),
  getJobDetail: (jobId) => api.get(`/admin/jobs/${jobId}`),
  retryJob: (jobId) => api.post(`/admin/jobs/${jobId}/retry`),
  resolveJob: (jobId, notes) => api.post(`/admin/jobs/${jobId}/resolve${notes ? `?notes=${encodeURIComponent(notes)}` : ''}`),
  
  // Settings
  getSettings: () => api.get('/admin/settings'),
  updateSettings: (data) => api.put('/admin/settings', data),
  toggleMaintenance: (enabled, message) => api.post(`/admin/settings/maintenance?enabled=${enabled}${message ? `&message=${encodeURIComponent(message)}` : ''}`),
  updateFeatureFlags: (flags) => api.put('/admin/settings/feature-flags', flags)
};

// Support API (User)
export const supportAPI = {
  createTicket: (subject, description, category) => 
    api.post('/support/tickets', { subject, description, category }),
  getTickets: () => api.get('/support/tickets'),
  getTicket: (ticketId) => api.get(`/support/tickets/${ticketId}`),
  addMessage: (ticketId, message) => api.post(`/support/tickets/${ticketId}/message`, { message })
};

// AI Keys API (BYO-AI)
export const aiKeysAPI = {
  getKeys: () => api.get('/ai-keys'),
  getProviders: () => api.get('/ai-keys/providers'),
  getUsage: () => api.get('/ai-keys/usage'),
  addKey: (provider, api_key) => api.post(`/ai-keys?provider=${provider}&api_key=${encodeURIComponent(api_key)}`),
  deleteKey: (provider) => api.delete(`/ai-keys/${provider}`),
  toggleKey: (provider, is_active) => api.put(`/ai-keys/${provider}/toggle?is_active=${is_active}`)
};

// Build API - SSE streaming build system
export const buildAPI = {
  // Start a new build job
  startBuild: (projectId, prompt, ai_provider = 'auto') => 
    api.post(`/projects/${projectId}/build`, { prompt, ai_provider }),
  
  // Get job status with recent events
  getJobStatus: (jobId) => api.get(`/jobs/${jobId}`),
  
  // Cancel a running job
  cancelJob: (jobId) => api.post(`/jobs/${jobId}/cancel`),
  
  // List project build jobs
  listProjectJobs: (projectId, limit = 10) => 
    api.get(`/projects/${projectId}/jobs?limit=${limit}`),
  
  // SSE stream URL (use with EventSource)
  getStreamUrl: (jobId) => {
    const token = api.defaults.headers.common['Authorization']?.replace('Bearer ', '');
    return `${API_BASE}/jobs/${jobId}/stream${token ? `?token=${token}` : ''}`;
  }
};

// Integrations API (GitHub, Vercel, etc.)
export const integrationsAPI = {
  // Get all integrations
  getIntegrations: () => api.get('/integrations'),
  getAllStatus: () => api.get('/integrations/all-status'),
  
  // GitHub OAuth
  getGitHubAuthUrl: () => api.get('/integrations/github/auth-url'),
  githubCallback: (code, state) => api.post(`/integrations/github/callback?code=${code}&state=${state}`),
  getGitHubStatus: () => api.get('/integrations/github/status'),
  disconnectGitHub: () => api.delete('/integrations/github'),
  
  // GitHub Repos
  listRepos: (page = 1, perPage = 30) => 
    api.get(`/integrations/github/repos?page=${page}&per_page=${perPage}`),
  createRepo: (name, description = '', isPrivate = false) => 
    api.post(`/integrations/github/repos?name=${encodeURIComponent(name)}&description=${encodeURIComponent(description)}&private=${isPrivate}`),
  getRepo: (owner, repo) => api.get(`/integrations/github/repos/${owner}/${repo}`),
  getRepoContents: (owner, repo, path = '') => 
    api.get(`/integrations/github/repos/${owner}/${repo}/contents?path=${encodeURIComponent(path)}`),
  getFileContent: (owner, repo, path) => 
    api.get(`/integrations/github/repos/${owner}/${repo}/file?path=${encodeURIComponent(path)}`),
  
  // Push to GitHub
  pushFile: (owner, repo, path, content, message = 'Update from Nirman AI') =>
    api.post(`/integrations/github/repos/${owner}/${repo}/push`, { path, content, message }),
  pushMultipleFiles: (owner, repo, files, message = 'Update from Nirman AI') =>
    api.post(`/integrations/github/repos/${owner}/${repo}/push-multiple`, { files, message }),
  
  // Deploy project
  deployToGitHub: (projectId, repoName = null, createNew = true, isPrivate = false, enablePages = true) =>
    api.post(`/integrations/github/deploy/${projectId}?create_new=${createNew}&private=${isPrivate}&enable_pages=${enablePages}${repoName ? `&repo_name=${encodeURIComponent(repoName)}` : ''}`),
  getDeployment: (projectId) => api.get(`/integrations/github/deployments/${projectId}`),
  
  // GitHub Pages
  getPagesStatus: (owner, repo) => api.get(`/integrations/github/repos/${owner}/${repo}/pages`),
  enablePages: (owner, repo) => api.post(`/integrations/github/repos/${owner}/${repo}/pages`),

  // Vercel
  getVercelAuthUrl: () => api.get('/integrations/vercel/auth-url'),
  vercelCallback: (code, state) => api.post(`/integrations/vercel/callback?code=${code}&state=${state}`),
  getVercelStatus: () => api.get('/integrations/vercel/status'),
  disconnectVercel: () => api.delete('/integrations/vercel'),
  getVercelProjects: () => api.get('/integrations/vercel/projects'),
  deployToVercel: (projectId) => api.post(`/integrations/vercel/deploy?project_id=${projectId}`),

  // Supabase
  connectSupabase: (accessToken, orgId) => api.post('/integrations/supabase/connect', { access_token: accessToken, org_id: orgId }),
  getSupabaseStatus: () => api.get('/integrations/supabase/status'),
  disconnectSupabase: () => api.delete('/integrations/supabase'),
  getSupabaseProjects: () => api.get('/integrations/supabase/projects'),
  createSupabaseProject: (name, orgId, region) => api.post('/integrations/supabase/projects', { name, organization_id: orgId, region }),

  // Firebase
  connectFirebase: (projectId, serviceAccountJson) => api.post('/integrations/firebase/connect', { project_id: projectId, service_account_json: serviceAccountJson }),
  getFirebaseStatus: () => api.get('/integrations/firebase/status'),
  disconnectFirebase: () => api.delete('/integrations/firebase'),
  deployToFirebase: (projectId) => api.post(`/integrations/firebase/deploy?project_id=${projectId}`),

  // MongoDB Atlas
  connectMongoDB: (publicKey, privateKey, groupId, orgId) => api.post('/integrations/mongodb/connect', { public_key: publicKey, private_key: privateKey, group_id: groupId, org_id: orgId }),
  getMongoDBStatus: () => api.get('/integrations/mongodb/status'),
  disconnectMongoDB: () => api.delete('/integrations/mongodb'),
  getMongoDBClusters: () => api.get('/integrations/mongodb/clusters'),
  createMongoDBCluster: (name, tier, region) => api.post('/integrations/mongodb/clusters', { name, tier, region }),

  // Canva
  getCanvaAuthUrl: () => api.get('/integrations/canva/auth-url'),
  canvaCallback: (code, state) => api.post(`/integrations/canva/callback?code=${code}&state=${state}`),
  getCanvaStatus: () => api.get('/integrations/canva/status'),
  disconnectCanva: () => api.delete('/integrations/canva'),
  getCanvaDesigns: () => api.get('/integrations/canva/designs'),
  createCanvaDesign: (type, title) => api.post('/integrations/canva/designs', { design_type: type, title }),

  // Razorpay
  connectRazorpay: (keyId, keySecret) => api.post('/integrations/razorpay/connect', { key_id: keyId, key_secret: keySecret }),
  getRazorpayStatus: () => api.get('/integrations/razorpay/status'),
  disconnectRazorpay: () => api.delete('/integrations/razorpay'),
  createRazorpayOrder: (amount, currency, receipt) => api.post('/integrations/razorpay/orders', { amount, currency, receipt }),
  verifyRazorpayPayment: (orderId, paymentId, signature) => api.post('/integrations/razorpay/verify', { order_id: orderId, payment_id: paymentId, signature }),

  // Cashfree
  connectCashfree: (appId, secretKey) => api.post('/integrations/cashfree/connect', { app_id: appId, secret_key: secretKey }),
  getCashfreeStatus: () => api.get('/integrations/cashfree/status'),
  disconnectCashfree: () => api.delete('/integrations/cashfree'),
  createCashfreeOrder: (orderId, amount, phone, email, returnUrl) => api.post('/integrations/cashfree/orders', { order_id: orderId, order_amount: amount, customer_phone: phone, customer_email: email, return_url: returnUrl }),
  createCashfreeQuickPayment: (amount, phone, email, returnUrl) => api.post('/integrations/cashfree/quick-payment', { amount, customer_phone: phone, customer_email: email, return_url: returnUrl })
};

// Agent Chat API - Single chat with SSE streaming
export const agentChatAPI = {
  // Send message and get job_id for streaming
  sendMessage: (message, projectId = null) => {
    const params = new URLSearchParams({ message });
    if (projectId) params.append('project_id', projectId);
    return api.post(`/agent/chat?${params.toString()}`);
  },
  
  // Get job details
  getJob: (jobId) => api.get(`/jobs/${jobId}`),
  
  // Get job events
  getJobEvents: (jobId, limit = 50) => api.get(`/jobs/${jobId}/events?limit=${limit}`),
  
  // Stop running job
  stopJob: (jobId) => api.post(`/jobs/${jobId}/stop`),
  
  // Get chat history
  getHistory: (limit = 50) => api.get(`/agent/history?limit=${limit}`),
  
  // Get user's jobs
  getJobs: (status = null, limit = 20) => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (status) params.append('status', status);
    return api.get(`/agent/jobs?${params.toString()}`);
  },
  
  // SSE stream URL
  getStreamUrl: (jobId) => {
    const token = api.defaults.headers.common['Authorization']?.replace('Bearer ', '');
    return `${API_BASE}/jobs/${jobId}/stream${token ? `?token=${token}` : ''}`;
  },
  
  // Get preview URL
  getPreviewUrl: (jobId) => `${API_BASE}/preview/${jobId}`
};

export default api;
