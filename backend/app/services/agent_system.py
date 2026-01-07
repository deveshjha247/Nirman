"""
Agent System - Multi-Agent Orchestrator
Intelligent agent routing and execution
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, AsyncGenerator
from enum import Enum

from app.db.mongo import db
from app.models.build import (
    BuildJob, BuildEvent, BuildStatus, AgentType, EventType,
    PlanStep, ChatMessage
)
from app.services.ai_router import call_ai_provider


class AgentRouter:
    """
    Routes queries to the appropriate agent based on intent.
    """
    
    # Intent classification patterns
    CODE_PATTERNS = [
        "write", "code", "script", "program", "create app", "build", "develop",
        "make a", "generate", "implement", "function", "class", "api",
        "website", "web app", "frontend", "backend", "database", "server",
        "python", "javascript", "react", "node", "html", "css"
    ]
    
    FILE_PATTERNS = [
        "file", "folder", "directory", "find", "locate", "search for",
        "move", "copy", "delete", "rename", "organize", "list files"
    ]
    
    WEB_PATTERNS = [
        "search", "browse", "look up", "find online", "google",
        "latest news", "weather", "stock", "price", "what is"
    ]
    
    MCP_PATTERNS = [
        "use mcp", "mcp tool", "model context", "external tool",
        "calendar", "email", "slack", "github api", "database query"
    ]
    
    @classmethod
    def classify_intent(cls, query: str) -> AgentType:
        """Classify user query to determine best agent"""
        query_lower = query.lower()
        
        # Check for explicit MCP request
        if any(p in query_lower for p in cls.MCP_PATTERNS):
            return AgentType.MCP
        
        # Check for code/build tasks
        if any(p in query_lower for p in cls.CODE_PATTERNS):
            return AgentType.CODER
        
        # Check for file operations
        if any(p in query_lower for p in cls.FILE_PATTERNS):
            return AgentType.FILE
        
        # Check for web/search tasks
        if any(p in query_lower for p in cls.WEB_PATTERNS):
            return AgentType.BROWSER
        
        # Default to casual for conversation
        return AgentType.CASUAL
    
    @classmethod
    def is_complex_task(cls, query: str) -> bool:
        """Determine if task needs planning (multiple steps)"""
        complexity_indicators = [
            "and then", "after that", "multiple", "several",
            "complete", "full", "entire", "project",
            "step by step", "workflow", "process"
        ]
        query_lower = query.lower()
        
        # Long queries are likely complex
        if len(query.split()) > 20:
            return True
        
        # Check for complexity indicators
        if any(ind in query_lower for ind in complexity_indicators):
            return True
        
        return False


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, name: str, agent_type: AgentType):
        self.name = name
        self.agent_type = agent_type
        self.status = "ready"
    
    async def process(self, prompt: str, context: Dict = None) -> AsyncGenerator[BuildEvent, None]:
        """Process a prompt and yield events"""
        raise NotImplementedError


class CasualAgent(BaseAgent):
    """Agent for casual conversation"""
    
    def __init__(self):
        super().__init__("Casual Agent", AgentType.CASUAL)
        self.system_prompt = """You are Nirman AI, a helpful and friendly AI assistant.
You can have casual conversations, answer questions, and help with various tasks.
Be concise but helpful. If the user wants to build something, suggest they describe what they want to create."""
    
    async def process(self, prompt: str, context: Dict = None) -> AsyncGenerator[BuildEvent, None]:
        job_id = context.get("job_id", str(uuid.uuid4()))
        
        yield BuildEvent(
            id=str(uuid.uuid4()),
            job_id=job_id,
            type=EventType.AGENT_THINKING,
            agent=self.agent_type,
            message="Thinking...",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Call AI
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = await call_ai_provider(
            messages=messages,
            provider=context.get("provider", "auto"),
            model=context.get("model", "auto")
        )
        
        yield BuildEvent(
            id=str(uuid.uuid4()),
            job_id=job_id,
            type=EventType.AI_MESSAGE,
            agent=self.agent_type,
            message=response.get("content", "I'm not sure how to help with that."),
            data={"model": response.get("model"), "provider": response.get("provider")},
            timestamp=datetime.now(timezone.utc).isoformat()
        )


class CoderAgent(BaseAgent):
    """Agent for code generation and execution"""
    
    def __init__(self):
        super().__init__("Coder Agent", AgentType.CODER)
        self.system_prompt = """You are Nirman AI's Code Agent, an expert programmer.
You can write, debug, and execute code in Python, JavaScript, TypeScript, HTML, CSS, and more.

When writing code:
1. Always wrap code in markdown code blocks with language specified
2. Write clean, well-commented code
3. Handle errors gracefully
4. Follow best practices for the language

For web projects, structure files properly:
- index.html for main HTML
- styles.css for CSS
- script.js or app.js for JavaScript
- Use modern frameworks when appropriate

Respond with your reasoning first, then provide the code."""
    
    async def process(self, prompt: str, context: Dict = None) -> AsyncGenerator[BuildEvent, None]:
        job_id = context.get("job_id", str(uuid.uuid4()))
        project_id = context.get("project_id")
        
        yield BuildEvent(
            id=str(uuid.uuid4()),
            job_id=job_id,
            type=EventType.AGENT_THINKING,
            agent=self.agent_type,
            message="Analyzing requirements and planning code...",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Build context with existing files if project exists
        files_context = ""
        if project_id:
            project = await db.projects.find_one({"id": project_id})
            if project and project.get("files"):
                files_context = "\n\nExisting project files:\n"
                for f in project.get("files", [])[:5]:
                    files_context += f"- {f.get('name')}: {f.get('description', 'No description')}\n"
        
        messages = [
            {"role": "system", "content": self.system_prompt + files_context},
            {"role": "user", "content": prompt}
        ]
        
        yield BuildEvent(
            id=str(uuid.uuid4()),
            job_id=job_id,
            type=EventType.CODE_GENERATING if "CODE_GENERATING" in dir(EventType) else EventType.AGENT_THINKING,
            agent=self.agent_type,
            message="Generating code...",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        response = await call_ai_provider(
            messages=messages,
            provider=context.get("provider", "auto"),
            model=context.get("model", "auto")
        )
        
        content = response.get("content", "")
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(content)
        files_created = []
        
        for i, block in enumerate(code_blocks):
            lang = block.get("language", "text")
            code = block.get("code", "")
            filename = block.get("filename") or self._infer_filename(lang, i)
            
            yield BuildEvent(
                id=str(uuid.uuid4()),
                job_id=job_id,
                type=EventType.FILE_CREATED,
                agent=self.agent_type,
                message=f"Created {filename}",
                data={"filename": filename, "language": lang, "code": code},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            files_created.append(filename)
        
        # Check if it's a web project for preview
        is_web_project = any(f.endswith(('.html', '.jsx', '.tsx')) for f in files_created)
        
        yield BuildEvent(
            id=str(uuid.uuid4()),
            job_id=job_id,
            type=EventType.AI_MESSAGE,
            agent=self.agent_type,
            message=content,
            data={
                "model": response.get("model"),
                "provider": response.get("provider"),
                "code_blocks": code_blocks,
                "files_created": files_created,
                "has_preview": is_web_project
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        if is_web_project:
            yield BuildEvent(
                id=str(uuid.uuid4()),
                job_id=job_id,
                type=EventType.PREVIEW_READY,
                agent=self.agent_type,
                message="Preview ready",
                data={"files": files_created},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    
    def _extract_code_blocks(self, content: str) -> List[Dict]:
        """Extract code blocks from markdown content"""
        blocks = []
        import re
        
        # Pattern for ```language\ncode\n```
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for i, (lang, code) in enumerate(matches):
            lang = lang or "text"
            # Try to extract filename from comment
            filename = None
            lines = code.strip().split('\n')
            if lines and ('filename:' in lines[0].lower() or 'file:' in lines[0].lower()):
                filename = lines[0].split(':')[-1].strip().strip('"\'')
                code = '\n'.join(lines[1:])
            
            blocks.append({
                "language": lang,
                "code": code.strip(),
                "filename": filename
            })
        
        return blocks
    
    def _infer_filename(self, lang: str, index: int) -> str:
        """Infer filename from language"""
        ext_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "html": ".html",
            "css": ".css",
            "json": ".json",
            "jsx": ".jsx",
            "tsx": ".tsx",
            "go": ".go",
            "rust": ".rs",
            "java": ".java",
            "c": ".c",
            "cpp": ".cpp",
            "bash": ".sh",
            "shell": ".sh",
            "sql": ".sql",
            "yaml": ".yaml",
            "yml": ".yml",
        }
        ext = ext_map.get(lang.lower(), ".txt")
        
        if lang.lower() == "html":
            return "index.html" if index == 0 else f"page{index}.html"
        elif lang.lower() == "css":
            return "styles.css" if index == 0 else f"styles{index}.css"
        elif lang.lower() in ["javascript", "js"]:
            return "script.js" if index == 0 else f"script{index}.js"
        elif lang.lower() == "python":
            return "main.py" if index == 0 else f"module{index}.py"
        else:
            return f"file{index}{ext}"


class PlannerAgent(BaseAgent):
    """Agent for planning complex multi-step tasks"""
    
    def __init__(self, agents: Dict[AgentType, BaseAgent]):
        super().__init__("Planner Agent", AgentType.PLANNER)
        self.agents = agents
        self.system_prompt = """You are Nirman AI's Planner Agent. You break down complex tasks into steps.

When given a task, create a plan with specific steps. Each step should be assigned to an agent:
- coder: For writing code, creating files, building features
- file: For file operations (create, move, delete, organize)
- browser: For web searches and information gathering
- casual: For explanations and conversations

Respond with a JSON plan in this format:
```json
{
  "plan": [
    {"id": "1", "agent": "coder", "task": "Create the HTML structure"},
    {"id": "2", "agent": "coder", "task": "Add CSS styling"},
    {"id": "3", "agent": "coder", "task": "Implement JavaScript functionality"}
  ]
}
```

Keep plans concise (3-5 steps for most tasks). Be specific in task descriptions."""
    
    async def process(self, prompt: str, context: Dict = None) -> AsyncGenerator[BuildEvent, None]:
        job_id = context.get("job_id", str(uuid.uuid4()))
        
        yield BuildEvent(
            id=str(uuid.uuid4()),
            job_id=job_id,
            type=EventType.AGENT_THINKING,
            agent=self.agent_type,
            message="Creating a plan...",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Get plan from AI
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Create a plan for: {prompt}"}
        ]
        
        response = await call_ai_provider(
            messages=messages,
            provider=context.get("provider", "auto"),
            model=context.get("model", "auto")
        )
        
        content = response.get("content", "")
        plan = self._parse_plan(content)
        
        if not plan:
            yield BuildEvent(
                id=str(uuid.uuid4()),
                job_id=job_id,
                type=EventType.AI_MESSAGE,
                agent=self.agent_type,
                message="I'll work on this directly without a complex plan.",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            # Fall back to coder agent
            async for event in self.agents[AgentType.CODER].process(prompt, context):
                yield event
            return
        
        yield BuildEvent(
            id=str(uuid.uuid4()),
            job_id=job_id,
            type=EventType.PLAN_CREATED,
            agent=self.agent_type,
            message=f"Created plan with {len(plan)} steps",
            data={"plan": plan},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Execute each step
        accumulated_context = context.copy() if context else {}
        accumulated_results = []
        
        for i, step in enumerate(plan):
            step_id = step.get("id", str(i + 1))
            agent_type_str = step.get("agent", "coder")
            task = step.get("task", "")
            
            try:
                agent_type = AgentType(agent_type_str)
            except:
                agent_type = AgentType.CODER
            
            yield BuildEvent(
                id=str(uuid.uuid4()),
                job_id=job_id,
                type=EventType.PLAN_STEP_STARTED,
                agent=agent_type,
                message=f"Step {step_id}: {task}",
                data={"step_id": step_id, "agent": agent_type_str, "task": task},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            # Get the agent
            agent = self.agents.get(agent_type, self.agents[AgentType.CODER])
            
            # Build task prompt with context from previous steps
            task_prompt = task
            if accumulated_results:
                task_prompt = f"Previous work:\n{chr(10).join(accumulated_results[-2:])}\n\nNow: {task}"
            
            # Execute step
            step_result = ""
            async for event in agent.process(task_prompt, accumulated_context):
                yield event
                if event.type == EventType.AI_MESSAGE:
                    step_result = event.message
            
            accumulated_results.append(f"Step {step_id}: {step_result[:200]}...")
            
            yield BuildEvent(
                id=str(uuid.uuid4()),
                job_id=job_id,
                type=EventType.PLAN_STEP_COMPLETED,
                agent=agent_type,
                message=f"Completed step {step_id}",
                data={"step_id": step_id},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    
    def _parse_plan(self, content: str) -> List[Dict]:
        """Parse plan from AI response"""
        import re
        
        # Try to find JSON in response
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return data.get("plan", [])
            except:
                pass
        
        # Try direct JSON parse
        try:
            data = json.loads(content)
            return data.get("plan", [])
        except:
            pass
        
        return []


class AgentOrchestrator:
    """
    Main orchestrator that manages agents and job execution.
    """
    
    def __init__(self):
        # Initialize agents
        self.casual_agent = CasualAgent()
        self.coder_agent = CoderAgent()
        
        self.agents = {
            AgentType.CASUAL: self.casual_agent,
            AgentType.CODER: self.coder_agent,
        }
        
        # Planner has access to all agents
        self.planner_agent = PlannerAgent(self.agents)
        self.agents[AgentType.PLANNER] = self.planner_agent
        
        # Active jobs
        self.active_jobs: Dict[str, asyncio.Task] = {}
    
    async def start_job(
        self,
        prompt: str,
        user_id: str,
        project_id: Optional[str] = None,
        model: str = "auto",
        provider: str = "auto"
    ) -> AsyncGenerator[BuildEvent, None]:
        """Start a new build job and stream events"""
        
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Create job record
        job = BuildJob(
            id=job_id,
            project_id=project_id,
            user_id=user_id,
            prompt=prompt,
            status=BuildStatus.QUEUED,
            model=model,
            provider=provider,
            created_at=now
        )
        
        # Save to DB
        await db.build_jobs.insert_one(job.dict())
        
        # Emit job started
        yield BuildEvent(
            id=str(uuid.uuid4()),
            job_id=job_id,
            type=EventType.JOB_STARTED,
            message="Job started",
            data={"job_id": job_id, "prompt": prompt},
            timestamp=now
        )
        
        # Update status
        await db.build_jobs.update_one(
            {"id": job_id},
            {"$set": {"status": BuildStatus.PLANNING, "started_at": now}}
        )
        
        # Route to appropriate agent
        intent = AgentRouter.classify_intent(prompt)
        is_complex = AgentRouter.is_complex_task(prompt)
        
        yield BuildEvent(
            id=str(uuid.uuid4()),
            job_id=job_id,
            type=EventType.AGENT_SELECTED,
            agent=AgentType.PLANNER if is_complex else intent,
            message=f"Selected {'Planner' if is_complex else intent.value} agent",
            data={"intent": intent.value, "is_complex": is_complex},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Update job with agent
        selected_agent = AgentType.PLANNER if is_complex else intent
        await db.build_jobs.update_one(
            {"id": job_id},
            {"$set": {"agent": selected_agent, "status": BuildStatus.RUNNING}}
        )
        
        # Process with agent
        context = {
            "job_id": job_id,
            "project_id": project_id,
            "user_id": user_id,
            "model": model,
            "provider": provider
        }
        
        agent = self.agents.get(selected_agent, self.casual_agent)
        files_created = []
        
        try:
            async for event in agent.process(prompt, context):
                # Save event to DB
                await db.build_events.insert_one(event.dict())
                
                # Track files
                if event.type == EventType.FILE_CREATED:
                    files_created.append(event.data.get("filename"))
                
                yield event
            
            # Job completed
            await db.build_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": BuildStatus.COMPLETED,
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "files_created": files_created,
                        "progress": 100
                    }
                }
            )
            
            yield BuildEvent(
                id=str(uuid.uuid4()),
                job_id=job_id,
                type=EventType.JOB_COMPLETED,
                message="Job completed successfully",
                data={"files_created": files_created},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            # Job failed
            await db.build_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": BuildStatus.FAILED,
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "error": str(e)
                    }
                }
            )
            
            yield BuildEvent(
                id=str(uuid.uuid4()),
                job_id=job_id,
                type=EventType.JOB_FAILED,
                message=f"Job failed: {str(e)}",
                data={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    
    async def stop_job(self, job_id: str) -> bool:
        """Stop a running job"""
        if job_id in self.active_jobs:
            self.active_jobs[job_id].cancel()
            del self.active_jobs[job_id]
        
        await db.build_jobs.update_one(
            {"id": job_id},
            {
                "$set": {
                    "status": BuildStatus.CANCELLED,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        return True
    
    async def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job details"""
        job = await db.build_jobs.find_one({"id": job_id}, {"_id": 0})
        return job
    
    async def get_job_events(self, job_id: str) -> List[Dict]:
        """Get all events for a job"""
        events = await db.build_events.find(
            {"job_id": job_id},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(1000)
        return events


# Global orchestrator instance
orchestrator = AgentOrchestrator()
