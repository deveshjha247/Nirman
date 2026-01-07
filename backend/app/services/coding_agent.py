"""
Nirman AI Builder - Pay-Per-Use Coding Agent with Smart Routing

Architecture:
- Agent Router: Selects best agent based on query complexity
- Coder Agent: Writes and executes code (Python, JS, Go, etc.)
- Planner Agent: Divides complex tasks into sub-tasks
- Browser Agent: Web scraping and research
- File Agent: File operations and management

Pay Model Integration:
- FREE: 100 requests/day, basic models
- BASIC: 1000 requests/day, GPT-4 Turbo
- PRO: Unlimited, all models + priority
"""

import asyncio
import uuid
import json
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.db.mongo import db
from app.services.ai_router import generate_code, MODEL_CONFIG


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class AgentType(str, Enum):
    CODER = "coder"
    PLANNER = "planner"
    BROWSER = "browser"
    FILE = "file"
    CASUAL = "casual"


class TaskComplexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    RUNNING = "running"


# Plan-based model selection
PLAN_MODELS = {
    "free": {
        "default_provider": "deepseek",
        "default_model": "deepseek-chat",
        "allowed_providers": ["deepseek", "groq"],
        "daily_limit": 100,
        "max_tokens": 4000,
    },
    "basic": {
        "default_provider": "openai",
        "default_model": "gpt-4o-mini",
        "allowed_providers": ["openai", "gemini", "deepseek", "groq", "mistral"],
        "daily_limit": 1000,
        "max_tokens": 8000,
    },
    "pro": {
        "default_provider": "openai",
        "default_model": "gpt-4o",
        "allowed_providers": list(MODEL_CONFIG.keys()),
        "daily_limit": -1,  # Unlimited
        "max_tokens": 16000,
    },
    "enterprise": {
        "default_provider": "claude",
        "default_model": "claude-sonnet-4-20250514",
        "allowed_providers": list(MODEL_CONFIG.keys()),
        "daily_limit": -1,
        "max_tokens": 32000,
    }
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ExecutionResult:
    """Result of code/tool execution"""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time_ms: int = 0
    tool_type: str = ""


@dataclass
class AgentTask:
    """A task to be executed by an agent"""
    id: str
    description: str
    agent_type: AgentType
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Response from an agent"""
    answer: str
    reasoning: str
    code_blocks: List[Dict[str, str]] = field(default_factory=list)
    execution_results: List[ExecutionResult] = field(default_factory=list)
    tokens_used: int = 0
    cost_estimate: float = 0.0


# =============================================================================
# AGENT PROMPTS
# =============================================================================

CODER_AGENT_PROMPT = """You are an expert autonomous coding agent. You can write, debug, and execute code in multiple languages.

CAPABILITIES:
- Python, JavaScript/TypeScript, Go, Java, C/C++, Rust, Ruby
- Full-stack web development (React, Vue, Node.js, FastAPI, Django)
- Database operations (SQL, MongoDB, Redis)
- API development and integration
- File operations and system commands

RULES:
1. Always wrap code in appropriate code blocks with language tag
2. For executable code, use this format:
   ```python:filename.py
   # code here
   ```
3. Explain your reasoning before writing code
4. Handle errors gracefully and suggest fixes
5. Follow best practices and write clean, maintainable code

OUTPUT FORMAT:
- First, briefly explain what you'll do (1-2 sentences)
- Then provide the code in properly formatted blocks
- If multiple files needed, create each separately
- For web apps, use Tailwind CSS for styling"""

PLANNER_AGENT_PROMPT = """You are a task planner that breaks down complex requests into manageable steps.

Your job is to analyze user requests and create a structured plan with:
1. Clear, actionable steps
2. Appropriate agent assignment for each step
3. Dependencies between steps
4. Estimated complexity

OUTPUT FORMAT (JSON):
{
    "goal": "Main objective",
    "complexity": "low|medium|high",
    "steps": [
        {
            "id": "step_1",
            "description": "What to do",
            "agent": "coder|browser|file|casual",
            "dependencies": [],
            "estimated_tokens": 500
        }
    ]
}

AGENT TYPES:
- coder: Write/execute code, build applications
- browser: Web search, scraping, research
- file: File operations, organization
- casual: General conversation, explanations"""

BROWSER_AGENT_PROMPT = """You are a web research agent that can search and extract information from the web.

CAPABILITIES:
- Search the web for information using search queries
- Extract structured data from web pages
- Summarize articles, documentation, and tutorials
- Find code examples, libraries, and best practices
- Research APIs, frameworks, and technologies
- Compare products, services, and solutions
- Find latest news and updates on topics

TOOLS AVAILABLE:
1. web_search(query) - Search the web for information
2. fetch_url(url) - Fetch and extract content from a URL
3. summarize(content) - Summarize long content

OUTPUT FORMAT:
```json
{
    "search_query": "your optimized search query",
    "action": "search|fetch|summarize",
    "reasoning": "why this action"
}
```

After research, provide:
- Clear summary of findings (bullet points)
- Relevant links and sources with descriptions
- Key facts and statistics
- Recommendations based on findings
- Code examples if applicable (in code blocks)

Be thorough but concise. Focus on actionable information."""

FILE_AGENT_PROMPT = """You are a file operations agent that manages files and directories.

CAPABILITIES:
- Create new files with content
- Read and display file contents
- Update/modify existing files
- Delete files and directories
- Organize files into directories
- Search for files by name or pattern
- Batch file operations (rename, move, copy)
- Generate file listings and directory trees
- Analyze file contents and structure

TOOLS AVAILABLE:
1. create_file(path, content) - Create a new file
2. read_file(path) - Read file contents
3. update_file(path, content) - Update existing file
4. delete_file(path) - Delete a file
5. list_dir(path) - List directory contents
6. search_files(pattern) - Search for files
7. move_file(src, dest) - Move/rename a file
8. copy_file(src, dest) - Copy a file

OUTPUT FORMAT for operations:
```json
{
    "operation": "create|read|update|delete|list|search|move|copy",
    "path": "/path/to/file",
    "content": "file content if applicable",
    "reasoning": "why this operation"
}
```

RULES:
1. Always confirm destructive operations (delete)
2. Create parent directories if needed
3. Handle errors gracefully
4. Provide clear feedback on operations performed
5. Suggest organization improvements when relevant

After operations, provide:
- List of operations performed with status
- File structure visualization if relevant
- Any errors or warnings
- Suggestions for improvement"""


# =============================================================================
# AGENT ROUTER - Smart Agent Selection
# =============================================================================

class AgentRouter:
    """
    Selects the appropriate agent based on query analysis.
    Uses few-shot classification for task routing.
    """
    
    # Task classification examples
    TASK_EXAMPLES = {
        "coder": [
            "write a python script",
            "create a react component",
            "build a web app",
            "debug this code",
            "make a snake game",
            "generate api endpoint",
            "implement authentication",
            "create database schema",
        ],
        "browser": [
            "search the web for",
            "find information about",
            "research",
            "look up",
            "what is the latest",
            "find tutorials on",
            "search online",
        ],
        "file": [
            "organize files",
            "find the file",
            "move files",
            "rename files",
            "create folder",
            "list directory",
            "delete files",
        ],
        "planner": [
            "create a plan for",
            "help me build a complete",
            "i need a full application",
            "design a system",
            "create architecture for",
            "build a project with multiple",
        ],
        "casual": [
            "hello",
            "how are you",
            "tell me about",
            "explain",
            "what is",
            "why does",
            "thanks",
        ],
    }
    
    # Complexity indicators
    COMPLEXITY_INDICATORS = {
        "high": [
            "multiple", "full stack", "complete application",
            "with database", "authentication", "deployment",
            "microservices", "api integration", "real-time",
        ],
        "medium": [
            "with", "including", "add", "integrate",
            "responsive", "interactive", "dynamic",
        ],
        "low": [
            "simple", "basic", "quick", "just",
            "small", "only", "single",
        ],
    }
    
    @classmethod
    def classify_task(cls, query: str) -> AgentType:
        """Classify query to determine best agent."""
        query_lower = query.lower()
        
        # Score each agent type
        scores = {agent: 0 for agent in AgentType}
        
        for agent_type, keywords in cls.TASK_EXAMPLES.items():
            for keyword in keywords:
                if keyword in query_lower:
                    scores[AgentType(agent_type)] += 1
        
        # Get highest scoring agent
        best_agent = max(scores, key=scores.get)
        
        # Default to coder if no clear match
        if scores[best_agent] == 0:
            return AgentType.CODER
        
        return best_agent
    
    @classmethod
    def estimate_complexity(cls, query: str) -> TaskComplexity:
        """Estimate task complexity."""
        query_lower = query.lower()
        
        for complexity, indicators in cls.COMPLEXITY_INDICATORS.items():
            for indicator in indicators:
                if indicator in query_lower:
                    return TaskComplexity(complexity)
        
        # Default to medium
        return TaskComplexity.MEDIUM
    
    @classmethod
    def should_use_planner(cls, query: str) -> bool:
        """Determine if planner agent should be used."""
        complexity = cls.estimate_complexity(query)
        agent_type = cls.classify_task(query)
        
        # Use planner for high complexity or explicit planner requests
        return (
            complexity == TaskComplexity.HIGH or 
            agent_type == AgentType.PLANNER
        )


# =============================================================================
# BASE AGENT CLASS
# =============================================================================

class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(
        self,
        name: str,
        agent_type: AgentType,
        system_prompt: str,
        provider: str = "auto",
        model: str = None,
    ):
        self.name = name
        self.agent_type = agent_type
        self.system_prompt = system_prompt
        self.provider = provider
        self.model = model
        self.memory: List[Dict[str, str]] = []
        self.tools: Dict[str, Any] = {}
    
    def add_to_memory(self, role: str, content: str):
        """Add message to agent memory."""
        self.memory.append({"role": role, "content": content})
    
    def clear_memory(self):
        """Clear agent memory."""
        self.memory = []
    
    def build_messages(self, user_prompt: str) -> List[Dict[str, str]]:
        """Build message list for LLM."""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.memory)
        messages.append({"role": "user", "content": user_prompt})
        return messages
    
    @abstractmethod
    async def process(
        self,
        prompt: str,
        user_id: str,
        user_plan: str = "free",
    ) -> AgentResponse:
        """Process user prompt and return response."""
        pass
    
    def extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extract code blocks from response."""
        pattern = r"```(\w+)?(?::([^\n]+))?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        blocks = []
        for match in matches:
            language = match[0] or "text"
            filename = match[1] or None
            code = match[2].strip()
            
            blocks.append({
                "language": language,
                "filename": filename,
                "code": code,
            })
        
        return blocks


# =============================================================================
# CODER AGENT
# =============================================================================

class CoderAgent(BaseAgent):
    """
    Agent that writes and executes code.
    Supports multiple languages with execution capabilities.
    """
    
    SUPPORTED_LANGUAGES = {
        "python": {"extension": ".py", "executable": True},
        "javascript": {"extension": ".js", "executable": True},
        "typescript": {"extension": ".ts", "executable": False},
        "html": {"extension": ".html", "executable": False},
        "css": {"extension": ".css", "executable": False},
        "go": {"extension": ".go", "executable": True},
        "java": {"extension": ".java", "executable": True},
        "rust": {"extension": ".rs", "executable": True},
        "bash": {"extension": ".sh", "executable": True},
        "sql": {"extension": ".sql", "executable": False},
    }
    
    def __init__(self, provider: str = "auto", model: str = None):
        super().__init__(
            name="Coder Agent",
            agent_type=AgentType.CODER,
            system_prompt=CODER_AGENT_PROMPT,
            provider=provider,
            model=model,
        )
    
    async def process(
        self,
        prompt: str,
        user_id: str,
        user_plan: str = "free",
    ) -> AgentResponse:
        """Process coding request."""
        
        # Get plan config
        plan_config = PLAN_MODELS.get(user_plan, PLAN_MODELS["free"])
        
        # Determine provider and model
        provider = self.provider if self.provider != "auto" else plan_config["default_provider"]
        model = self.model or plan_config["default_model"]
        
        # Build messages
        messages = self.build_messages(prompt)
        
        # Generate code
        result = await generate_code(
            prompt=prompt,
            provider=provider,
            model=model,
            user_id=user_id,
            job_id=str(uuid.uuid4()),
            system_prompt=self.system_prompt,
            conversation_history=[],
            max_tokens=plan_config["max_tokens"],
        )
        
        if not result["success"]:
            return AgentResponse(
                answer=f"Error: {result.get('error', 'Unknown error')}",
                reasoning="Code generation failed",
                tokens_used=0,
                cost_estimate=0.0,
            )
        
        # Extract code blocks
        code = result.get("code", "")
        code_blocks = self.extract_code_blocks(code)
        
        # Add to memory
        self.add_to_memory("assistant", code)
        
        return AgentResponse(
            answer=code,
            reasoning=f"Generated code using {provider}/{model}",
            code_blocks=code_blocks,
            tokens_used=result.get("tokens_in", 0) + result.get("tokens_out", 0),
            cost_estimate=result.get("cost_estimate", 0.0),
        )


# =============================================================================
# BROWSER AGENT - Web Research & Information Extraction
# =============================================================================

class BrowserAgent(BaseAgent):
    """
    Agent that performs web research and information extraction.
    Can search the web, fetch URLs, and summarize content.
    """
    
    def __init__(self, provider: str = "auto", model: str = None):
        super().__init__(
            name="Browser Agent",
            agent_type=AgentType.BROWSER,
            system_prompt=BROWSER_AGENT_PROMPT,
            provider=provider,
            model=model,
        )
        self.search_results_cache: Dict[str, Any] = {}
    
    async def process(
        self,
        prompt: str,
        user_id: str,
        user_plan: str = "free",
    ) -> AgentResponse:
        """Process web research request."""
        
        # Get plan config
        plan_config = PLAN_MODELS.get(user_plan, PLAN_MODELS["free"])
        provider = self.provider if self.provider != "auto" else plan_config["default_provider"]
        model = self.model or plan_config["default_model"]
        
        # Build research prompt
        research_prompt = f"""Research Request: {prompt}

Please help me research this topic. Provide:
1. A comprehensive summary of the topic
2. Key facts and information
3. Relevant resources and references
4. Code examples if applicable
5. Best practices and recommendations

Structure your response clearly with sections."""
        
        # Generate research response
        result = await generate_code(
            prompt=research_prompt,
            provider=provider,
            model=model,
            user_id=user_id,
            job_id=str(uuid.uuid4()),
            system_prompt=self.system_prompt,
            conversation_history=[],
            max_tokens=plan_config["max_tokens"],
        )
        
        if not result["success"]:
            return AgentResponse(
                answer=f"Error during research: {result.get('error', 'Unknown error')}",
                reasoning="Web research failed",
                tokens_used=0,
                cost_estimate=0.0,
            )
        
        answer = result.get("code", "")
        code_blocks = self.extract_code_blocks(answer)
        
        # Extract any URLs/links mentioned
        urls = self._extract_urls(answer)
        
        # Add metadata about sources
        if urls:
            answer += "\n\n---\n**Sources Found:**\n"
            for url in urls[:10]:  # Limit to 10 URLs
                answer += f"- {url}\n"
        
        self.add_to_memory("assistant", answer)
        
        return AgentResponse(
            answer=answer,
            reasoning=f"Web research completed using {provider}/{model}",
            code_blocks=code_blocks,
            tokens_used=result.get("tokens_in", 0) + result.get("tokens_out", 0),
            cost_estimate=result.get("cost_estimate", 0.0),
        )
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)
    
    async def web_search(self, query: str) -> Dict[str, Any]:
        """
        Perform a web search (simulated with AI knowledge).
        In production, integrate with actual search API (SearxNG, Google, etc.)
        """
        # For now, return AI-generated search simulation
        # TODO: Integrate with real search API like SearxNG
        return {
            "query": query,
            "results": [],
            "status": "simulated",
            "note": "Integrate with SearxNG for real search results"
        }
    
    async def fetch_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch and extract content from a URL.
        In production, use httpx/aiohttp with proper parsing.
        """
        # TODO: Implement actual URL fetching with httpx
        return {
            "url": url,
            "content": "",
            "status": "not_implemented",
            "note": "URL fetching to be implemented"
        }


# =============================================================================
# FILE AGENT - File Operations & Management
# =============================================================================

class FileAgent(BaseAgent):
    """
    Agent that performs file operations and management.
    Can create, read, update, delete files and organize directories.
    """
    
    ALLOWED_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
        ".json", ".yaml", ".yml", ".md", ".txt", ".csv", ".xml",
        ".go", ".java", ".c", ".cpp", ".h", ".rs", ".rb", ".php",
        ".sql", ".sh", ".bash", ".env", ".gitignore", ".dockerfile",
    }
    
    def __init__(self, provider: str = "auto", model: str = None):
        super().__init__(
            name="File Agent",
            agent_type=AgentType.FILE,
            system_prompt=FILE_AGENT_PROMPT,
            provider=provider,
            model=model,
        )
        self.operations_log: List[Dict[str, Any]] = []
    
    async def process(
        self,
        prompt: str,
        user_id: str,
        user_plan: str = "free",
    ) -> AgentResponse:
        """Process file operation request."""
        
        # Get plan config
        plan_config = PLAN_MODELS.get(user_plan, PLAN_MODELS["free"])
        provider = self.provider if self.provider != "auto" else plan_config["default_provider"]
        model = self.model or plan_config["default_model"]
        
        # Build file operation prompt
        file_prompt = f"""File Operation Request: {prompt}

Analyze this request and determine:
1. What file operations are needed
2. What files/directories are involved
3. What content to create/modify

Provide the operations in a clear, executable format.
For each file operation, show:
- The operation type (create/read/update/delete/list/move)
- The file path
- The content (if applicable)

Use code blocks for file contents with the filename:
```language:path/to/file.ext
content here
```"""
        
        # Generate file operations response
        result = await generate_code(
            prompt=file_prompt,
            provider=provider,
            model=model,
            user_id=user_id,
            job_id=str(uuid.uuid4()),
            system_prompt=self.system_prompt,
            conversation_history=[],
            max_tokens=plan_config["max_tokens"],
        )
        
        if not result["success"]:
            return AgentResponse(
                answer=f"Error processing file operation: {result.get('error', 'Unknown error')}",
                reasoning="File operation failed",
                tokens_used=0,
                cost_estimate=0.0,
            )
        
        answer = result.get("code", "")
        code_blocks = self.extract_code_blocks(answer)
        
        # Parse and validate file operations
        operations = self._parse_file_operations(answer, code_blocks)
        
        # Add operations summary
        if operations:
            answer += "\n\n---\n**Operations Summary:**\n"
            for op in operations:
                status_icon = "✅" if op.get("valid", True) else "⚠️"
                answer += f"{status_icon} {op['operation'].upper()}: `{op.get('path', 'N/A')}`\n"
        
        self.add_to_memory("assistant", answer)
        
        return AgentResponse(
            answer=answer,
            reasoning=f"File operations processed using {provider}/{model}",
            code_blocks=code_blocks,
            execution_results=[
                ExecutionResult(
                    success=op.get("valid", True),
                    output=f"{op['operation']}: {op.get('path', '')}",
                    tool_type="file"
                )
                for op in operations
            ],
            tokens_used=result.get("tokens_in", 0) + result.get("tokens_out", 0),
            cost_estimate=result.get("cost_estimate", 0.0),
        )
    
    def _parse_file_operations(
        self, 
        text: str, 
        code_blocks: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Parse file operations from response."""
        operations = []
        
        # Extract operations from code blocks with filenames
        for block in code_blocks:
            if block.get("filename"):
                operations.append({
                    "operation": "create",
                    "path": block["filename"],
                    "content": block["code"],
                    "language": block["language"],
                    "valid": self._validate_path(block["filename"]),
                })
        
        # Look for JSON operation blocks
        json_pattern = r"```json\s*(\{.*?\})\s*```"
        json_matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in json_matches:
            try:
                op_data = json.loads(match)
                if "operation" in op_data:
                    operations.append({
                        **op_data,
                        "valid": self._validate_operation(op_data),
                    })
            except json.JSONDecodeError:
                pass
        
        return operations
    
    def _validate_path(self, path: str) -> bool:
        """Validate file path for safety."""
        # Check for directory traversal
        if ".." in path:
            return False
        
        # Check extension
        ext = "." + path.split(".")[-1] if "." in path else ""
        if ext and ext.lower() not in self.ALLOWED_EXTENSIONS:
            return False
        
        return True
    
    def _validate_operation(self, operation: Dict[str, Any]) -> bool:
        """Validate a file operation."""
        op_type = operation.get("operation", "").lower()
        path = operation.get("path", "")
        
        # Validate operation type
        valid_ops = {"create", "read", "update", "delete", "list", "search", "move", "copy"}
        if op_type not in valid_ops:
            return False
        
        # Validate path
        if path and not self._validate_path(path):
            return False
        
        return True
    
    async def create_file(self, path: str, content: str) -> Dict[str, Any]:
        """Create a new file with content."""
        if not self._validate_path(path):
            return {"success": False, "error": "Invalid file path"}
        
        # Log operation (actual file creation would happen here)
        self.operations_log.append({
            "operation": "create",
            "path": path,
            "content_length": len(content),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        return {
            "success": True,
            "path": path,
            "operation": "create",
            "message": f"File created: {path}"
        }
    
    async def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """List directory contents."""
        # This would interact with actual filesystem in production
        return {
            "success": True,
            "path": path,
            "operation": "list",
            "contents": [],
            "note": "Directory listing simulated"
        }


# =============================================================================
# CASUAL AGENT - General Conversation
# =============================================================================

class CasualAgent(BaseAgent):
    """
    Agent for general conversation and explanations.
    Handles non-technical queries and provides helpful responses.
    """
    
    CASUAL_PROMPT = """You are a helpful, friendly AI assistant.

CAPABILITIES:
- Answer general questions
- Explain concepts clearly
- Have casual conversations
- Provide advice and suggestions
- Help with brainstorming

RULES:
1. Be friendly and conversational
2. Give clear, concise answers
3. Ask clarifying questions if needed
4. Be helpful and supportive
5. If asked about coding, suggest using the coding agent

Keep responses natural and engaging."""
    
    def __init__(self, provider: str = "auto", model: str = None):
        super().__init__(
            name="Casual Agent",
            agent_type=AgentType.CASUAL,
            system_prompt=self.CASUAL_PROMPT,
            provider=provider,
            model=model,
        )
    
    async def process(
        self,
        prompt: str,
        user_id: str,
        user_plan: str = "free",
    ) -> AgentResponse:
        """Process casual conversation request."""
        
        # Get plan config
        plan_config = PLAN_MODELS.get(user_plan, PLAN_MODELS["free"])
        provider = self.provider if self.provider != "auto" else plan_config["default_provider"]
        model = self.model or plan_config["default_model"]
        
        # Generate response
        result = await generate_code(
            prompt=prompt,
            provider=provider,
            model=model,
            user_id=user_id,
            job_id=str(uuid.uuid4()),
            system_prompt=self.system_prompt,
            conversation_history=[],
            max_tokens=min(plan_config["max_tokens"], 2000),  # Limit for casual chat
        )
        
        if not result["success"]:
            return AgentResponse(
                answer=f"Sorry, I had trouble responding: {result.get('error', 'Unknown error')}",
                reasoning="Casual response failed",
                tokens_used=0,
                cost_estimate=0.0,
            )
        
        answer = result.get("code", "")
        self.add_to_memory("assistant", answer)
        
        return AgentResponse(
            answer=answer,
            reasoning=f"Casual response using {provider}/{model}",
            code_blocks=[],
            tokens_used=result.get("tokens_in", 0) + result.get("tokens_out", 0),
            cost_estimate=result.get("cost_estimate", 0.0),
        )


# =============================================================================
# PLANNER AGENT
# =============================================================================

class PlannerAgent(BaseAgent):
    """
    Agent that plans and coordinates complex tasks.
    Divides work among multiple agents.
    """
    
    def __init__(self, provider: str = "auto", model: str = None):
        super().__init__(
            name="Planner Agent",
            agent_type=AgentType.PLANNER,
            system_prompt=PLANNER_AGENT_PROMPT,
            provider=provider,
            model=model,
        )
        
        # Sub-agents
        self.agents = {
            AgentType.CODER: CoderAgent(),
            AgentType.BROWSER: BrowserAgent(),
            AgentType.FILE: FileAgent(),
            AgentType.CASUAL: CasualAgent(),
        }
    
    async def process(
        self,
        prompt: str,
        user_id: str,
        user_plan: str = "free",
    ) -> AgentResponse:
        """Create and execute plan for complex task."""
        
        # Get plan config
        plan_config = PLAN_MODELS.get(user_plan, PLAN_MODELS["free"])
        provider = self.provider if self.provider != "auto" else plan_config["default_provider"]
        model = self.model or plan_config["default_model"]
        
        # Step 1: Generate plan
        plan_prompt = f"""Analyze this request and create an execution plan:

USER REQUEST: {prompt}

Create a JSON plan with steps, agent assignments, and dependencies.
Focus on actionable, specific steps that can be executed."""
        
        plan_result = await generate_code(
            prompt=plan_prompt,
            provider=provider,
            model=model,
            user_id=user_id,
            job_id=str(uuid.uuid4()),
            system_prompt=self.system_prompt,
            conversation_history=[],
            max_tokens=2000,
        )
        
        if not plan_result["success"]:
            return AgentResponse(
                answer=f"Error creating plan: {plan_result.get('error', 'Unknown error')}",
                reasoning="Planning failed",
                tokens_used=0,
                cost_estimate=0.0,
            )
        
        # Parse plan
        plan_text = plan_result.get("code", "")
        plan_json = self._extract_json(plan_text)
        
        if not plan_json:
            # Fallback: Treat as single coder task
            coder = self.agents[AgentType.CODER]
            return await coder.process(prompt, user_id, user_plan)
        
        # Step 2: Execute plan steps
        total_tokens = plan_result.get("tokens_in", 0) + plan_result.get("tokens_out", 0)
        total_cost = plan_result.get("cost_estimate", 0.0)
        all_results = []
        
        steps = plan_json.get("steps", [])
        for step in steps:
            agent_type = AgentType(step.get("agent", "coder"))
            agent = self.agents.get(agent_type)
            
            if agent:
                step_result = await agent.process(
                    step["description"],
                    user_id,
                    user_plan,
                )
                all_results.append({
                    "step": step["id"],
                    "description": step["description"],
                    "result": step_result.answer,
                })
                total_tokens += step_result.tokens_used
                total_cost += step_result.cost_estimate
        
        # Combine results
        combined_answer = self._combine_results(plan_json, all_results)
        
        return AgentResponse(
            answer=combined_answer,
            reasoning=f"Executed {len(steps)} steps using planner",
            code_blocks=[],
            tokens_used=total_tokens,
            cost_estimate=total_cost,
        )
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from text."""
        try:
            # Try to find JSON block
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try direct parse
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
        return None
    
    def _combine_results(
        self,
        plan: Dict,
        results: List[Dict],
    ) -> str:
        """Combine step results into final response."""
        output = f"## Completed: {plan.get('goal', 'Task')}\n\n"
        
        for result in results:
            output += f"### Step: {result['description']}\n"
            output += result["result"]
            output += "\n\n---\n\n"
        
        return output


# =============================================================================
# MAIN CODING AGENT SERVICE
# =============================================================================

class CodingAgentService:
    """
    Main service for the coding agent system.
    Handles request routing, agent selection, and billing.
    """
    
    def __init__(self):
        self.router = AgentRouter()
        self.agents = {
            AgentType.CODER: CoderAgent(),
            AgentType.PLANNER: PlannerAgent(),
            AgentType.BROWSER: BrowserAgent(),
            AgentType.FILE: FileAgent(),
            AgentType.CASUAL: CasualAgent(),
        }
    
    async def process_request(
        self,
        prompt: str,
        user_id: str,
        project_id: Optional[str] = None,
        provider: str = "auto",
        model: str = None,
        agent_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a coding agent request.
        
        1. Check user plan and limits
        2. Route to appropriate agent
        3. Execute and track usage
        4. Return result
        """
        
        # Get user info
        user = await db.users.find_one({"id": user_id})
        if not user:
            return {"success": False, "error": "User not found"}
        
        user_plan = user.get("plan", "free")
        plan_config = PLAN_MODELS.get(user_plan, PLAN_MODELS["free"])
        
        # Check daily limit
        if not await self._check_daily_limit(user_id, plan_config):
            return {
                "success": False,
                "error": "Daily request limit reached. Upgrade your plan for more requests.",
                "limit_reached": True,
            }
        
        # Determine agent based on query analysis or explicit type
        if agent_type:
            # Use explicitly specified agent type
            try:
                selected_type = AgentType(agent_type)
                agent = self.agents.get(selected_type, self.agents[AgentType.CODER])
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid agent type: {agent_type}. Valid types: coder, browser, file, planner, casual",
                }
        elif self.router.should_use_planner(prompt):
            agent = self.agents[AgentType.PLANNER]
        else:
            # Route to appropriate agent
            selected_type = self.router.classify_task(prompt)
            agent = self.agents.get(selected_type, self.agents[AgentType.CODER])
        
        # Set provider/model if specified
        if provider != "auto":
            if provider not in plan_config["allowed_providers"]:
                return {
                    "success": False,
                    "error": f"Provider '{provider}' not available on your plan. Allowed: {plan_config['allowed_providers']}",
                }
            agent.provider = provider
        
        if model:
            agent.model = model
        
        # Process request
        try:
            response = await agent.process(prompt, user_id, user_plan)
            
            # Track usage
            await self._track_usage(
                user_id=user_id,
                project_id=project_id,
                agent_type=agent.agent_type.value,
                tokens_used=response.tokens_used,
                cost=response.cost_estimate,
            )
            
            return {
                "success": True,
                "answer": response.answer,
                "reasoning": response.reasoning,
                "code_blocks": response.code_blocks,
                "tokens_used": response.tokens_used,
                "cost_estimate": response.cost_estimate,
                "agent_type": agent.agent_type.value,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def _check_daily_limit(
        self,
        user_id: str,
        plan_config: Dict,
    ) -> bool:
        """Check if user is within daily limit."""
        if plan_config["daily_limit"] == -1:
            return True  # Unlimited
        
        # Count today's requests
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        
        count = await db.ai_runs.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": today_start},
        })
        
        return count < plan_config["daily_limit"]
    
    async def _track_usage(
        self,
        user_id: str,
        project_id: Optional[str],
        agent_type: str,
        tokens_used: int,
        cost: float,
    ):
        """Track AI usage for billing."""
        usage_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "project_id": project_id,
            "agent_type": agent_type,
            "tokens_used": tokens_used,
            "cost_estimate": cost,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await db.ai_runs.insert_one(usage_doc)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

coding_agent_service = CodingAgentService()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def process_coding_request(
    prompt: str,
    user_id: str,
    project_id: Optional[str] = None,
    provider: str = "auto",
    model: str = None,
    agent_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to process coding requests.
    Use this in routes.
    
    Args:
        prompt: User's request
        user_id: User ID
        project_id: Optional project ID
        provider: AI provider (auto, openai, gemini, etc.)
        model: Specific model to use
        agent_type: Force specific agent (coder, browser, file, planner, casual)
    """
    return await coding_agent_service.process_request(
        prompt=prompt,
        user_id=user_id,
        project_id=project_id,
        provider=provider,
        model=model,
        agent_type=agent_type,
    )


async def get_agent_status(user_id: str) -> Dict[str, Any]:
    """Get agent status and usage info for user."""
    user = await db.users.find_one({"id": user_id})
    if not user:
        return {"error": "User not found"}
    
    user_plan = user.get("plan", "free")
    plan_config = PLAN_MODELS.get(user_plan, PLAN_MODELS["free"])
    
    # Count today's requests
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()
    
    today_count = await db.ai_runs.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": today_start},
    })
    
    # Total usage
    total_usage = await db.ai_runs.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_tokens": {"$sum": "$tokens_used"},
            "total_cost": {"$sum": "$cost_estimate"},
            "total_requests": {"$sum": 1},
        }},
    ]).to_list(1)
    
    usage_stats = total_usage[0] if total_usage else {
        "total_tokens": 0,
        "total_cost": 0,
        "total_requests": 0,
    }
    
    return {
        "plan": user_plan,
        "daily_limit": plan_config["daily_limit"],
        "requests_today": today_count,
        "requests_remaining": (
            plan_config["daily_limit"] - today_count 
            if plan_config["daily_limit"] != -1 
            else "unlimited"
        ),
        "allowed_providers": plan_config["allowed_providers"],
        "default_provider": plan_config["default_provider"],
        "default_model": plan_config["default_model"],
        "total_tokens_used": usage_stats.get("total_tokens", 0),
        "total_cost": usage_stats.get("total_cost", 0),
        "total_requests": usage_stats.get("total_requests", 0),
    }
