import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Docs = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeSection, setActiveSection] = useState('introduction');
  const [searchQuery, setSearchQuery] = useState('');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Parse section from URL hash
  useEffect(() => {
    const updateSection = () => {
      const hash = location.hash.replace('#', '');
      if (hash) {
        setActiveSection(hash);
      }
    };
    updateSection();
  }, [location]);

  const sections = [
    {
      id: 'getting-started',
      title: 'Getting Started',
      icon: '🚀',
      items: [
        { id: 'introduction', title: 'Introduction' },
        { id: 'quickstart', title: 'Quick Start' },
        { id: 'installation', title: 'Installation' },
        { id: 'authentication', title: 'Authentication' }
      ]
    },
    {
      id: 'core-concepts',
      title: 'Core Concepts',
      icon: '💡',
      items: [
        { id: 'projects', title: 'Projects' },
        { id: 'ai-providers', title: 'AI Providers' },
        { id: 'build-system', title: 'Build System' },
        { id: 'templates', title: 'Templates' }
      ]
    },
    {
      id: 'llm-keys',
      title: 'LLM Keys',
      icon: '🔑',
      items: [
        { id: 'universal-keys', title: 'Universal Keys' },
        { id: 'key-management', title: 'Key Management' },
        { id: 'credits-system', title: 'Credits System' },
        { id: 'rate-limits', title: 'Rate Limits' }
      ]
    },
    {
      id: 'api-reference',
      title: 'API Reference',
      icon: '📚',
      items: [
        { id: 'api-overview', title: 'Overview' },
        { id: 'api-auth', title: 'Authentication API' },
        { id: 'api-projects', title: 'Projects API' },
        { id: 'api-build', title: 'Build API' },
        { id: 'api-llm-keys', title: 'LLM Keys API' }
      ]
    },
    {
      id: 'integrations',
      title: 'Integrations',
      icon: '🔗',
      items: [
        { id: 'github', title: 'GitHub' },
        { id: 'vercel', title: 'Vercel' },
        { id: 'firebase', title: 'Firebase' },
        { id: 'supabase', title: 'Supabase' }
      ]
    },
    {
      id: 'guides',
      title: 'Guides',
      icon: '📖',
      items: [
        { id: 'build-landing-page', title: 'Build a Landing Page' },
        { id: 'deploy-github', title: 'Deploy to GitHub' },
        { id: 'custom-domains', title: 'Custom Domains' },
        { id: 'best-practices', title: 'Best Practices' }
      ]
    }
  ];

  const content = {
    introduction: {
      title: 'Introduction to Nirman',
      content: `
# Welcome to Nirman 🚀

**Nirman** (निर्माण = "Creation" in Hindi) is an AI-powered web app builder that transforms your ideas into fully functional websites in seconds.

## What is Nirman?

Nirman is a platform that uses cutting-edge AI models to generate production-ready websites from natural language descriptions. Simply describe what you want, and our AI agents will:

1. **Plan** - Analyze your requirements and create a detailed specification
2. **Build** - Generate clean, modern HTML/CSS/JavaScript code
3. **Deploy** - One-click deployment to GitHub Pages or Vercel

## Key Features

- **🤖 17+ AI Providers** - Choose from OpenAI, Gemini, Claude, and more
- **🔑 Universal LLM Keys** - One API key for all providers
- **⚡ Real-time Preview** - See changes as they happen
- **🐙 GitHub Integration** - Deploy with one click
- **🧠 Self-Learning** - AI that learns from your preferences

## Who is it for?

- **Entrepreneurs** - Launch MVPs in hours, not weeks
- **Designers** - Prototype ideas instantly
- **Developers** - Accelerate your workflow 10x
- **Students** - Build portfolio projects easily

## Getting Started

Ready to build something amazing? Let's get started!

\`\`\`bash
# Sign up at nirman.tech
# Create your first project
# Describe what you want to build
# Watch the magic happen! ✨
\`\`\`
      `
    },
    quickstart: {
      title: 'Quick Start Guide',
      content: `
# Quick Start Guide

Get up and running with Nirman in under 5 minutes!

## Step 1: Create an Account

1. Go to [nirman.tech](https://nirman.tech)
2. Click "Get Started"
3. Sign up with your email

## Step 2: Create Your First Project

\`\`\`javascript
// From the dashboard, click "New Project"
// Give it a name like "My Landing Page"
// Choose a framework (React, HTML, etc.)
\`\`\`

## Step 3: Describe Your Website

In the chat interface, describe what you want:

\`\`\`
"Build a modern landing page for a SaaS product called TaskFlow.
It should have:
- Hero section with a tagline
- Features section with 3 cards
- Pricing table with 3 plans
- Contact form
Use a blue and purple color scheme."
\`\`\`

## Step 4: Watch the Magic

Nirman will:
1. ✅ Analyze your requirements
2. ✅ Generate a detailed plan
3. ✅ Build the complete website
4. ✅ Show you a live preview

## Step 5: Deploy

Click "Deploy to GitHub" to:
- Create a new repository
- Push all the code
- Enable GitHub Pages
- Get a live URL!

## Next Steps

- Learn about [AI Providers](/docs#ai-providers)
- Set up [Universal LLM Keys](/docs#universal-keys)
- Explore [Templates](/docs#templates)
      `
    },
    'universal-keys': {
      title: 'Universal LLM Keys',
      content: `
# Universal LLM Keys 🔑

Universal LLM Keys allow you to use multiple AI providers with a single API key.

## What are Universal Keys?

Instead of managing separate API keys for OpenAI, Gemini, Claude, etc., you get **one key** that works with all providers:

\`\`\`
nk_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
\`\`\`

## Benefits

| Feature | Traditional | Universal Key |
|---------|-------------|---------------|
| Keys to manage | 5-10+ | 1 |
| Billing | Multiple invoices | Single wallet |
| Provider switching | Code changes | Just change model |
| Rate limiting | Per provider | Unified |

## Creating a Key

1. Go to Dashboard → LLM Keys
2. Click "Create New Key"
3. Name your key (e.g., "Production")
4. Select allowed providers
5. **Save the key immediately** - it's shown only once!

## Using Your Key

### With OpenAI SDK

\`\`\`python
import openai

client = openai.OpenAI(
    api_key="nk_your_key_here",
    base_url="https://api.nirman.tech/v1"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
\`\`\`

### With cURL

\`\`\`bash
curl https://api.nirman.tech/v1/chat/completions \\
  -H "Authorization: Bearer nk_your_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
\`\`\`

### With JavaScript

\`\`\`javascript
const response = await fetch('https://api.nirman.tech/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer nk_your_key_here',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-4o',
    messages: [{ role: 'user', content: 'Hello!' }]
  })
});
\`\`\`

## Supported Models

| Provider | Models |
|----------|--------|
| OpenAI | gpt-5.2, gpt-4o, gpt-4o-mini |
| Gemini | gemini-2.5-flash, gemini-2.5-pro |
| Claude | claude-sonnet-4, claude-3.5-sonnet |
| DeepSeek | deepseek-chat, deepseek-coder |
| Groq | llama-3.3-70b, mixtral-8x7b |
| Mistral | mistral-large, codestral |

## Pricing

Credits are charged per token used:

| Model | Input (per 1K) | Output (per 1K) |
|-------|----------------|-----------------|
| gpt-4o | $0.005 | $0.015 |
| gemini-2.5-flash | $0.0001 | $0.0004 |
| claude-sonnet-4 | $0.003 | $0.015 |
| deepseek-chat | $0.00014 | $0.00028 |
      `
    },
    'key-management': {
      title: 'Key Management',
      content: `
# Key Management

Learn how to manage your Universal LLM Keys effectively.

## Key Operations

### Create a Key

\`\`\`bash
POST /api/llm-keys
{
  "name": "Production Key",
  "allowed_providers": ["openai", "gemini", "claude"]
}
\`\`\`

### List Keys

\`\`\`bash
GET /api/llm-keys
\`\`\`

### Rotate a Key

When you need a new key string (for security):

\`\`\`bash
POST /api/llm-keys/{key_id}/regenerate
\`\`\`

**Note:** This invalidates the old key immediately!

### Delete a Key

\`\`\`bash
DELETE /api/llm-keys/{key_id}
\`\`\`

## Best Practices

### 1. Use Separate Keys for Environments

\`\`\`
Production Key → nk_prod_xxxxx
Development Key → nk_dev_xxxxx  
Testing Key → nk_test_xxxxx
\`\`\`

### 2. Set Rate Limits

Configure per-key rate limits to prevent abuse:

\`\`\`json
{
  "rate_limit_per_minute": 60,
  "rate_limit_per_day": 10000
}
\`\`\`

### 3. Monitor Usage

Check the usage dashboard regularly:
- Requests per day
- Cost breakdown by provider
- Error rates

### 4. Rotate Keys Periodically

For security, rotate production keys every 90 days.

## Security Tips

- ❌ Never commit keys to git
- ❌ Never expose keys in frontend code
- ✅ Use environment variables
- ✅ Enable key-specific IP restrictions (Enterprise)
- ✅ Set up usage alerts
      `
    },
    'credits-system': {
      title: 'Credits System',
      content: `
# Credits System

Understanding how credits work in Nirman.

## What are Credits?

Credits are the currency used to pay for AI API calls. 1 credit = $1 USD worth of API usage.

## Adding Credits

### From Wallet

1. Go to LLM Keys page
2. Click "Add Credits" on your key
3. Enter amount
4. Confirm (uses wallet balance)

### Direct Purchase

Buy credit packages with bonus:

| Amount | Price | Bonus |
|--------|-------|-------|
| $5 | $5 | - |
| $10 | $10 | +$0.50 |
| $25 | $25 | +$2 |
| $50 | $50 | +$5 |
| $100 | $100 | +$15 |

## How Credits are Used

Each API call deducts credits based on tokens used:

\`\`\`
Cost = (input_tokens / 1000 × input_price) + (output_tokens / 1000 × output_price)
\`\`\`

### Example Calculation

Using GPT-4o with 1000 input tokens and 500 output tokens:

\`\`\`
Cost = (1000/1000 × $0.005) + (500/1000 × $0.015)
     = $0.005 + $0.0075
     = $0.0125
\`\`\`

## Free Tier

New users get **$1 free credits** to try the platform!

This is enough for approximately:
- 200 requests with GPT-4o-mini
- 50 requests with GPT-4o
- 10,000 requests with Gemini Flash

## Monitoring Usage

Track your spending in real-time:

\`\`\`bash
GET /api/llm-keys/{key_id}/usage?days=30
\`\`\`

Response includes:
- Total requests
- Total cost
- Breakdown by provider
- Breakdown by model
      `
    },
    'api-overview': {
      title: 'API Overview',
      content: `
# API Overview

Nirman provides a RESTful API for all platform features.

## Base URL

\`\`\`
https://api.nirman.tech/api
\`\`\`

## Authentication

All API requests require a JWT token:

\`\`\`bash
Authorization: Bearer <your_jwt_token>
\`\`\`

Get a token by logging in:

\`\`\`bash
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "your_password"
}
\`\`\`

## Response Format

All responses follow this format:

\`\`\`json
{
  "data": { ... },
  "message": "Success",
  "status": "ok"
}
\`\`\`

Errors:

\`\`\`json
{
  "detail": "Error message here",
  "status_code": 400
}
\`\`\`

## Rate Limits

| Plan | Requests/min | Requests/day |
|------|--------------|--------------|
| Free | 60 | 1,000 |
| Pro | 300 | 10,000 |
| Enterprise | 1000 | Unlimited |

## Common Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/login | Login |
| GET | /auth/me | Get current user |
| GET | /projects | List projects |
| POST | /projects | Create project |
| POST | /projects/{id}/build | Start build |
| GET | /llm-keys | List LLM keys |
| POST | /llm-keys | Create LLM key |

## SDKs

Coming soon:
- Python SDK
- JavaScript/Node SDK
- Go SDK
      `
    },
    'api-llm-keys': {
      title: 'LLM Keys API',
      content: `
# LLM Keys API Reference

Complete API reference for Universal LLM Keys.

## List Keys

\`\`\`bash
GET /api/llm-keys
\`\`\`

**Response:**
\`\`\`json
[
  {
    "id": "uuid",
    "name": "Production Key",
    "key_preview": "nk_****xxxx",
    "is_active": true,
    "credits_balance": 25.50,
    "credits_used": 14.30,
    "total_requests": 1234,
    "allowed_providers": ["openai", "gemini", "claude"],
    "created_at": "2025-01-01T00:00:00Z"
  }
]
\`\`\`

## Create Key

\`\`\`bash
POST /api/llm-keys
Content-Type: application/json

{
  "name": "My New Key",
  "allowed_providers": ["openai", "gemini"]
}
\`\`\`

**Response:**
\`\`\`json
{
  "message": "LLM Key created successfully",
  "key": "nk_a1b2c3d4e5f6...",
  "key_id": "uuid",
  "warning": "Save this key! It won't be shown again."
}
\`\`\`

## Get Key Details

\`\`\`bash
GET /api/llm-keys/{key_id}
\`\`\`

## Update Key

\`\`\`bash
PUT /api/llm-keys/{key_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "is_active": true,
  "rate_limit_per_minute": 100,
  "allowed_providers": ["openai", "gemini", "claude"]
}
\`\`\`

## Delete Key

\`\`\`bash
DELETE /api/llm-keys/{key_id}
\`\`\`

## Regenerate Key

\`\`\`bash
POST /api/llm-keys/{key_id}/regenerate
\`\`\`

**Response:**
\`\`\`json
{
  "message": "Key regenerated successfully",
  "key": "nk_new_key_here...",
  "warning": "Save this key! It won't be shown again."
}
\`\`\`

## Add Credits

\`\`\`bash
POST /api/llm-keys/{key_id}/add-credits
Content-Type: application/json

{
  "amount": 25.00,
  "payment_method": "wallet"
}
\`\`\`

## Get Usage Stats

\`\`\`bash
GET /api/llm-keys/{key_id}/usage?days=30
\`\`\`

**Response:**
\`\`\`json
{
  "total_requests": 5000,
  "total_tokens_in": 1500000,
  "total_tokens_out": 750000,
  "total_cost": 12.50,
  "by_provider": {
    "openai": { "requests": 3000, "cost": 8.00 },
    "gemini": { "requests": 2000, "cost": 4.50 }
  },
  "by_model": {
    "gpt-4o": { "requests": 2000, "cost": 6.00 },
    "gpt-4o-mini": { "requests": 1000, "cost": 2.00 }
  }
}
\`\`\`

## Get Pricing Info

\`\`\`bash
GET /api/llm-keys/pricing/info
\`\`\`
      `
    },
    'ai-providers': {
      title: 'AI Providers',
      content: `
# AI Providers

Nirman supports 17+ AI providers for code generation.

## US/Global Providers

| Provider | Best For | Models |
|----------|----------|--------|
| **OpenAI** | Highest quality | GPT-5.2, GPT-4o, GPT-4o-mini |
| **Google Gemini** | Speed + Cost | Gemini 2.5 Flash, Gemini 2.5 Pro |
| **Anthropic Claude** | Creative, detailed | Claude Sonnet 4, Claude 3.5 |
| **xAI Grok** | Fast, conversational | Grok-2 |
| **Mistral** | European, balanced | Mistral Large, Codestral |
| **Cohere** | Enterprise, RAG | Command R+ |
| **Groq** | Ultra-fast inference | Llama 3.3 70B |

## Chinese AI Providers

| Provider | Best For | Models |
|----------|----------|--------|
| **DeepSeek** | Coding, cost-effective | DeepSeek Chat, DeepSeek Coder |
| **Alibaba Qwen** | Multilingual | Qwen Max, Qwen Plus |
| **Moonshot** | Long context (128K) | Moonshot V1 |
| **01.AI Yi** | Creative writing | Yi Lightning |
| **Zhipu GLM** | Chinese enterprise | GLM-4 Plus |

## Open Source

| Provider | Models |
|----------|--------|
| **Hugging Face** | Llama 3.3, Qwen 2.5, Mixtral, DeepSeek R1 |
| **Together AI** | Various open source models |
| **Fireworks AI** | Llama, Qwen, DeepSeek |

## Choosing a Provider

### For Best Quality
→ OpenAI GPT-5.2 or Claude Sonnet 4

### For Speed + Cost
→ Gemini 2.5 Flash or Groq

### For Coding Tasks
→ DeepSeek Coder or Codestral

### For Long Documents
→ Moonshot 128K or Gemini Pro
      `
    },
    github: {
      title: 'GitHub Integration',
      content: `
# GitHub Integration

Deploy your Nirman projects directly to GitHub.

## Connect Your Account

1. Go to Dashboard → Integrations
2. Click "Connect GitHub"
3. Authorize Nirman
4. Done! 🎉

## Deploy a Project

### Method 1: One-Click Deploy

1. Open your project
2. Click "Deploy" button
3. Choose "GitHub Pages"
4. Enter repository name
5. Click "Deploy"

Your site will be live at: \`username.github.io/repo-name\`

### Method 2: API Deploy

\`\`\`bash
POST /api/integrations/github/deploy/{project_id}
{
  "repo_name": "my-awesome-site",
  "create_new": true,
  "private": false,
  "enable_pages": true
}
\`\`\`

## Features

- ✅ Create new repositories
- ✅ Push code automatically
- ✅ Enable GitHub Pages
- ✅ Get live URL instantly
- ✅ Update existing repos

## GitHub Pages Settings

After deployment, your site is configured with:
- Source: main branch
- Path: / (root)
- HTTPS: Enabled

## Custom Domains

1. Go to your repository Settings
2. Navigate to Pages
3. Enter your custom domain
4. Add DNS records:

\`\`\`
Type: CNAME
Name: www
Value: username.github.io
\`\`\`
      `
    },
    'build-landing-page': {
      title: 'Build a Landing Page',
      content: `
# Guide: Build a Landing Page

Step-by-step guide to creating a beautiful landing page.

## Step 1: Create Project

\`\`\`
Name: "TaskFlow Landing"
Framework: HTML + Tailwind
\`\`\`

## Step 2: Write Your Prompt

\`\`\`
Create a modern SaaS landing page for "TaskFlow" - a task management app.

Sections needed:
1. **Hero**: Catchy headline, subtext, CTA button, hero image placeholder
2. **Features**: 3 feature cards with icons
3. **How it Works**: 3 steps with numbers
4. **Testimonials**: 3 customer quotes
5. **Pricing**: Free, Pro ($9/mo), Enterprise ($29/mo)
6. **FAQ**: 5 common questions
7. **Footer**: Links, social icons

Style:
- Color scheme: Blue (#3B82F6) and Purple (#8B5CF6) gradient
- Modern, clean, lots of whitespace
- Subtle animations on scroll
- Mobile responsive
\`\`\`

## Step 3: Review & Iterate

After the first build, you might want changes:

\`\`\`
"Make the hero section taller, add a background pattern.
Change the CTA button to say 'Start Free Trial'.
Add a 14-day free trial badge."
\`\`\`

## Step 4: Add Real Content

Replace placeholder content:

\`\`\`
"Update the testimonials with these real quotes:
1. 'TaskFlow doubled our productivity!' - Sarah, Acme Inc
2. 'Best tool we've ever used.' - John, StartupXYZ
3. 'Simple yet powerful.' - Mike, TechCorp"
\`\`\`

## Step 5: Deploy

\`\`\`
1. Click Deploy → GitHub Pages
2. Repository: taskflow-landing
3. Wait 1-2 minutes
4. Visit: yourusername.github.io/taskflow-landing
\`\`\`

## Pro Tips

- 🎨 Be specific about colors and fonts
- 📱 Always mention "mobile responsive"
- 🖼️ Use placeholder.com for images
- ⚡ Ask for animations to make it pop
      `
    }
  };

  const renderContent = (sectionId) => {
    const sectionContent = content[sectionId];
    if (!sectionContent) {
      return (
        <div className="prose prose-purple max-w-none">
          <h1>Coming Soon</h1>
          <p>This documentation section is being written. Check back soon!</p>
        </div>
      );
    }

    // Simple markdown-like rendering
    const renderMarkdown = (text) => {
      return text
        .split('\n')
        .map((line, i) => {
          // Headers
          if (line.startsWith('# ')) {
            return <h1 key={i} className="text-4xl font-bold text-gray-900 mb-6 mt-8">{line.substring(2)}</h1>;
          }
          if (line.startsWith('## ')) {
            return <h2 key={i} className="text-2xl font-bold text-gray-900 mb-4 mt-8">{line.substring(3)}</h2>;
          }
          if (line.startsWith('### ')) {
            return <h3 key={i} className="text-xl font-semibold text-gray-900 mb-3 mt-6">{line.substring(4)}</h3>;
          }
          
          // Code blocks
          if (line.startsWith('```')) {
            return null; // Handle in multiline
          }
          
          // List items
          if (line.startsWith('- ')) {
            return (
              <li key={i} className="ml-4 text-gray-700 mb-2 flex items-start gap-2">
                <span className="text-purple-600">•</span>
                <span dangerouslySetInnerHTML={{ __html: formatInlineCode(line.substring(2)) }} />
              </li>
            );
          }
          if (line.match(/^\d+\. /)) {
            return (
              <li key={i} className="ml-4 text-gray-700 mb-2">
                <span dangerouslySetInnerHTML={{ __html: formatInlineCode(line) }} />
              </li>
            );
          }
          
          // Tables
          if (line.startsWith('|')) {
            return null; // Handle separately
          }
          
          // Empty lines
          if (line.trim() === '') {
            return <br key={i} />;
          }
          
          // Regular paragraphs
          return (
            <p key={i} className="text-gray-700 mb-4 leading-relaxed">
              <span dangerouslySetInnerHTML={{ __html: formatInlineCode(line) }} />
            </p>
          );
        });
    };

    const formatInlineCode = (text) => {
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
        .replace(/`(.*?)`/g, '<code class="px-2 py-0.5 bg-gray-100 rounded text-sm font-mono text-purple-700">$1</code>')
        .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" class="text-purple-600 hover:text-purple-700 underline">$1</a>')
        .replace(/→/g, '<span class="text-purple-600">→</span>')
        .replace(/✅/g, '<span class="text-green-600">✅</span>')
        .replace(/❌/g, '<span class="text-red-600">❌</span>');
    };

    // Extract code blocks
    const renderWithCodeBlocks = (text) => {
      const parts = text.split(/(```[\s\S]*?```)/g);
      return parts.map((part, index) => {
        if (part.startsWith('```')) {
          const lines = part.split('\n');
          const lang = lines[0].replace('```', '').trim();
          const code = lines.slice(1, -1).join('\n');
          return (
            <pre key={index} className="bg-gray-900 text-green-400 p-4 rounded-xl overflow-x-auto my-4 text-sm">
              <code>{code}</code>
            </pre>
          );
        }
        return <div key={index}>{renderMarkdown(part)}</div>;
      });
    };

    // Extract tables
    const renderWithTables = (text) => {
      const tableRegex = /(\|.*\|[\r\n]+)+/g;
      const parts = text.split(tableRegex);
      
      return parts.map((part, index) => {
        if (part.includes('|') && part.split('\n').filter(l => l.trim().startsWith('|')).length > 1) {
          const rows = part.split('\n').filter(r => r.trim().startsWith('|'));
          if (rows.length < 2) return renderWithCodeBlocks(part);
          
          const headers = rows[0].split('|').filter(c => c.trim()).map(c => c.trim());
          const dataRows = rows.slice(2).map(r => r.split('|').filter(c => c.trim()).map(c => c.trim()));
          
          return (
            <div key={index} className="overflow-x-auto my-6">
              <table className="min-w-full border border-gray-200 rounded-xl overflow-hidden">
                <thead className="bg-purple-50">
                  <tr>
                    {headers.map((h, i) => (
                      <th key={i} className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-b border-gray-200">
                        <span dangerouslySetInnerHTML={{ __html: formatInlineCode(h) }} />
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dataRows.map((row, ri) => (
                    <tr key={ri} className={ri % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      {row.map((cell, ci) => (
                        <td key={ci} className="px-4 py-3 text-sm text-gray-700 border-b border-gray-100">
                          <span dangerouslySetInnerHTML={{ __html: formatInlineCode(cell) }} />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        return <div key={index}>{renderWithCodeBlocks(part)}</div>;
      });
    };

    return (
      <div className="prose prose-purple max-w-none">
        {renderWithTables(sectionContent.content)}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-2xl border-b border-gray-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/')} className="flex items-center gap-3 hover:opacity-80 transition">
              <img src="/logo.png" alt="Nirman Logo" className="w-10 h-10 rounded-xl shadow-md" />
              <span className="text-xl font-bold text-gray-900">Nirman</span>
            </button>
            <span className="text-gray-300 mx-2">|</span>
            <span className="text-gray-600 font-medium">Documentation</span>
          </div>
          
          {/* Search */}
          <div className="hidden md:flex items-center flex-1 max-w-md mx-8">
            <div className="relative w-full">
              <input
                type="text"
                placeholder="Search docs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 pl-10 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300"
              />
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <a href="https://github.com/nirman-ai" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-gray-900 transition">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
              </svg>
            </a>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-5 py-2 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-xl text-sm font-semibold hover:from-purple-700 hover:to-violet-700 transition-all shadow-md"
            >
              Dashboard
            </button>
          </div>
        </div>
      </header>

      <div className="pt-20 flex">
        {/* Sidebar */}
        <aside className="hidden lg:block fixed left-0 top-20 bottom-0 w-72 bg-gray-50/50 border-r border-gray-100 overflow-y-auto">
          <nav className="p-6">
            {sections.map((section) => (
              <div key={section.id} className="mb-6">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-3">
                  <span>{section.icon}</span>
                  {section.title}
                </h3>
                <ul className="space-y-1">
                  {section.items.map((item) => (
                    <li key={item.id}>
                      <button
                        onClick={() => {
                          setActiveSection(item.id);
                          window.history.pushState(null, '', `#${item.id}`);
                        }}
                        className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                          activeSection === item.id
                            ? 'bg-purple-100 text-purple-700 font-medium'
                            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                        }`}
                      >
                        {item.title}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </nav>
        </aside>

        {/* Mobile sidebar toggle */}
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="lg:hidden fixed bottom-6 left-6 z-50 p-3 bg-purple-600 text-white rounded-full shadow-lg"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Mobile sidebar */}
        {isMobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 z-50 bg-black/50" onClick={() => setIsMobileMenuOpen(false)}>
            <aside className="absolute left-0 top-0 bottom-0 w-72 bg-white shadow-xl overflow-y-auto" onClick={e => e.stopPropagation()}>
              <nav className="p-6 pt-20">
                {sections.map((section) => (
                  <div key={section.id} className="mb-6">
                    <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-3">
                      <span>{section.icon}</span>
                      {section.title}
                    </h3>
                    <ul className="space-y-1">
                      {section.items.map((item) => (
                        <li key={item.id}>
                          <button
                            onClick={() => {
                              setActiveSection(item.id);
                              setIsMobileMenuOpen(false);
                            }}
                            className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                              activeSection === item.id
                                ? 'bg-purple-100 text-purple-700 font-medium'
                                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                            }`}
                          >
                            {item.title}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </nav>
            </aside>
          </div>
        )}

        {/* Main content */}
        <main className="flex-1 lg:ml-72 min-h-screen">
          <div className="max-w-4xl mx-auto px-6 py-12">
            {renderContent(activeSection)}
            
            {/* Navigation */}
            <div className="mt-16 pt-8 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <a href="#" className="text-purple-600 hover:text-purple-700 text-sm font-medium">
                  ← Previous
                </a>
                <a href="#" className="text-purple-600 hover:text-purple-700 text-sm font-medium">
                  Next →
                </a>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Docs;
