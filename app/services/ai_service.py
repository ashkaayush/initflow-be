"""
AI service using Agno framework for multi-agent orchestration
"""
from typing import Dict, Any, Optional, List
from app.models import User
from app.config import settings
import os
from agno import Agent, Workflow, Task
from agno.models import Ollama, Gemini
import json


class AIService:
    """Service for AI interactions using Agno framework"""
    
    def __init__(self):
        # Initialize Agno models based on tier
        self.models = {
            "free": Ollama(
                model="llama3", 
                max_tokens=2048,
                host=settings.ollama_host
            ),
            "pro": Gemini(
                model="gemini-2.0-flash-exp", 
                max_tokens=4096,
                api_key=settings.google_api_key
            ),
            "premium": Gemini(
                model="gemini-2.0-flash-exp", 
                max_tokens=8192,
                api_key=settings.google_api_key
            )
        }
        
        # Initialize specialized agents
        self._init_agents()
    
    def _init_agents(self):
        """Initialize Agno agents for different tasks"""
        
        # Design Agent for UI/UX tasks
        self.design_agent = Agent(
            name="DesignAgent",
            role="UI/UX Designer and React Native Developer",
            goal="Create beautiful, functional, and accessible React Native components",
            backstory="""You are an expert UI/UX designer and React Native developer with years of experience 
            creating mobile applications. You understand modern design principles, accessibility standards, 
            and React Native best practices. You create components that are both visually appealing and 
            highly functional.""",
            tools=[],
            verbose=True
        )
        
        # Backend Agent for API and database tasks
        self.backend_agent = Agent(
            name="BackendAgent", 
            role="Backend Developer and API Architect",
            goal="Design and implement robust backend systems and APIs",
            backstory="""You are a senior backend developer with expertise in FastAPI, Supabase, 
            and modern API design. You create scalable, secure, and well-documented backend systems 
            that integrate seamlessly with mobile applications.""",
            tools=[],
            verbose=True
        )
        
        # Testing Agent for quality assurance
        self.testing_agent = Agent(
            name="TestingAgent",
            role="QA Engineer and Test Automation Specialist", 
            goal="Ensure code quality through comprehensive testing strategies",
            backstory="""You are a quality assurance expert who believes in test-driven development. 
            You create comprehensive test suites that catch bugs early and ensure code reliability. 
            You understand both unit testing and integration testing for mobile applications.""",
            tools=[],
            verbose=True
        )
        
        # Chat Agent for general assistance
        self.chat_agent = Agent(
            name="ChatAgent",
            role="AI Development Assistant",
            goal="Provide helpful guidance and assistance for mobile app development",
            backstory="""You are a friendly and knowledgeable AI assistant specializing in mobile 
            app development. You help developers understand their code, debug issues, and implement 
            new features. You communicate clearly and provide actionable advice.""",
            tools=[],
            verbose=True
        )
    
    async def generate_response(
        self, 
        user: User, 
        prompt: str, 
        context: Optional[Dict] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate AI response using Agno chat agent"""
        model = self.models.get(user.tier, self.models["free"])
        self.chat_agent.llm = model
        
        # Create context-aware prompt
        full_prompt = prompt
        if context:
            context_str = f"Project Context: {json.dumps(context, indent=2)}\n\n"
            full_prompt = context_str + prompt
        
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {full_prompt}"
        
        # Create and execute task
        task = Task(
            description=full_prompt,
            agent=self.chat_agent,
            expected_output="A helpful and detailed response to the user's question or request"
        )
        
        # Create workflow and execute
        workflow = Workflow(
            agents=[self.chat_agent],
            tasks=[task],
            verbose=True
        )
        
        result = workflow.kickoff()
        return result
    
    async def generate_code(
        self, 
        user: User, 
        task_description: str, 
        agent_type: str,
        project_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate code using appropriate Agno agent"""
        model = self.models.get(user.tier, self.models["free"])
        
        # Select appropriate agent
        if agent_type == "design":
            agent = self.design_agent
            agent.llm = model
            return await self._generate_design_code(task_description, project_context, user.tier)
        elif agent_type == "backend":
            agent = self.backend_agent
            agent.llm = model
            return await self._generate_backend_code(task_description, project_context, user.tier)
        elif agent_type == "testing":
            agent = self.testing_agent
            agent.llm = model
            return await self._generate_testing_code(task_description, project_context, user.tier)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    async def _generate_design_code(
        self, 
        task_description: str, 
        project_context: Optional[Dict],
        user_tier: str
    ) -> Dict[str, Any]:
        """Generate React Native UI components using Design Agent"""
        
        context_str = ""
        if project_context:
            context_str = f"Project Context: {json.dumps(project_context, indent=2)}\n\n"
        
        prompt = f"""{context_str}Task: {task_description}

Create a React Native component that implements the requested functionality. 
Consider the user's tier ({user_tier}) when determining the complexity and features to include.

For free tier: Create basic, functional components
For pro tier: Add TypeScript, animations, and advanced features
For premium tier: Include comprehensive TypeScript, custom hooks, animations, and accessibility features

Provide the component code and any necessary supporting files."""
        
        task = Task(
            description=prompt,
            agent=self.design_agent,
            expected_output="React Native component code with proper styling and functionality"
        )
        
        workflow = Workflow(
            agents=[self.design_agent],
            tasks=[task],
            verbose=True
        )
        
        result = workflow.kickoff()
        
        # Parse the result and format as expected
        return {
            "files": {
                "components/GeneratedComponent.js": result,
            },
            "reasoning": f"Generated React Native component using Agno Design Agent for: {task_description}"
        }
    
    async def _generate_backend_code(
        self, 
        task_description: str, 
        project_context: Optional[Dict],
        user_tier: str
    ) -> Dict[str, Any]:
        """Generate backend code using Backend Agent"""
        
        context_str = ""
        if project_context:
            context_str = f"Project Context: {json.dumps(project_context, indent=2)}\n\n"
        
        prompt = f"""{context_str}Task: {task_description}

Create backend code (API endpoints, database schemas, services) for the requested functionality.
Use FastAPI and Supabase as the primary technologies.
Consider the user's tier ({user_tier}) when determining features and complexity.

Provide complete, production-ready code with proper error handling and documentation."""
        
        task = Task(
            description=prompt,
            agent=self.backend_agent,
            expected_output="Backend code including API endpoints and database schemas"
        )
        
        workflow = Workflow(
            agents=[self.backend_agent],
            tasks=[task],
            verbose=True
        )
        
        result = workflow.kickoff()
        
        return {
            "files": {
                "api/generated_endpoints.py": result,
            },
            "reasoning": f"Generated backend code using Agno Backend Agent for: {task_description}"
        }
    
    async def _generate_testing_code(
        self, 
        task_description: str, 
        project_context: Optional[Dict],
        user_tier: str
    ) -> Dict[str, Any]:
        """Generate test code using Testing Agent"""
        
        context_str = ""
        if project_context:
            context_str = f"Project Context: {json.dumps(project_context, indent=2)}\n\n"
        
        prompt = f"""{context_str}Task: {task_description}

Create comprehensive test suites for the requested functionality.
Include unit tests, integration tests, and any necessary mocking.
Consider the user's tier ({user_tier}) when determining test coverage and complexity.

Provide complete test files with proper setup, teardown, and assertions."""
        
        task = Task(
            description=prompt,
            agent=self.testing_agent,
            expected_output="Comprehensive test suite with unit and integration tests"
        )
        
        workflow = Workflow(
            agents=[self.testing_agent],
            tasks=[task],
            verbose=True
        )
        
        result = workflow.kickoff()
        
        return {
            "files": {
                "__tests__/generated.test.js": result,
            },
            "reasoning": f"Generated test suite using Agno Testing Agent for: {task_description}"
        }
    
    async def coordinate_agents(
        self,
        user: User,
        tasks: List[Dict[str, Any]],
        project_context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Coordinate multiple agents working on related tasks"""
        model = self.models.get(user.tier, self.models["free"])
        
        # Set model for all agents
        self.design_agent.llm = model
        self.backend_agent.llm = model
        self.testing_agent.llm = model
        
        # Create tasks for each agent
        agno_tasks = []
        agents_used = []
        
        for task_data in tasks:
            agent_type = task_data.get("agent_type")
            description = task_data.get("description")
            
            if agent_type == "design":
                agent = self.design_agent
            elif agent_type == "backend":
                agent = self.backend_agent
            elif agent_type == "testing":
                agent = self.testing_agent
            else:
                continue
            
            context_str = ""
            if project_context:
                context_str = f"Project Context: {json.dumps(project_context, indent=2)}\n\n"
            
            task = Task(
                description=f"{context_str}{description}",
                agent=agent,
                expected_output=f"Code implementation for {agent_type} task"
            )
            
            agno_tasks.append(task)
            agents_used.append(agent)
        
        # Create coordinated workflow
        if agno_tasks:
            workflow = Workflow(
                agents=agents_used,
                tasks=agno_tasks,
                verbose=True
            )
            
            results = workflow.kickoff()
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results if isinstance(results, list) else [results]):
                formatted_results.append({
                    "agent_type": tasks[i].get("agent_type"),
                    "files": {f"generated_{i}.js": result},
                    "reasoning": f"Generated by Agno {tasks[i].get('agent_type')} agent"
                })
            
            return formatted_results
        
        return []


# Singleton instance
ai_service = AIService()