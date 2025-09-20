"""
Simplified Pipeline Orchestrator without async dependencies
For Streamlit compatibility
"""

import os
import json
import time
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

import requests


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineMode(Enum):
    QUICK = "quick_mode"
    ANALYSIS = "analysis_mode"
    FULL = "full_pipeline"


@dataclass
class PipelineStep:
    name: str
    component: str
    status: StepStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0


@dataclass
class PipelineExecution:
    execution_id: str
    mode: PipelineMode
    status: StepStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    steps: List[PipelineStep] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []


class SimplePipelineOrchestrator:
    """
    Simplified pipeline orchestrator for Streamlit compatibility
    """
    
    def __init__(self, config_path: str = "pipeline_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.session = self._setup_http_session()
        self.execution_history: List[PipelineExecution] = []
        
    def _load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            # Return default config if file not found
            return self._get_default_config()
        except json.JSONDecodeError as e:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "sequence": {
                "steps": [
                    {
                        "name": "summarize",
                        "component": "seeya",
                        "enabled": True,
                        "endpoint": "/api/summarize",
                        "timeout": 30,
                        "retry_count": 3,
                        "required_fields": ["user_id", "platform", "message_text", "timestamp"],
                        "output_fields": ["summary_id", "summary", "intent", "urgency", "type"]
                    },
                    {
                        "name": "process_summary",
                        "component": "sankalp",
                        "enabled": True,
                        "endpoint": "/api/process_summary",
                        "timeout": 25,
                        "retry_count": 3,
                        "required_fields": ["summary_id", "summary", "intent", "urgency", "user_id"],
                        "output_fields": ["task_id", "task_summary", "priority", "status"]
                    },
                    {
                        "name": "respond",
                        "component": "noopur",
                        "enabled": True,
                        "endpoint": "/api/respond",
                        "timeout": 20,
                        "retry_count": 2,
                        "required_fields": ["task_id", "user_id"],
                        "output_fields": ["response_id", "response_text", "tone", "status"]
                    }
                ]
            },
            "routing": {
                "default_flow": ["summarize", "process_summary", "respond"],
                "bypass_modes": {
                    "quick_mode": ["summarize", "respond"],
                    "analysis_mode": ["summarize", "search_similar", "metrics"],
                    "full_pipeline": ["summarize", "process_summary", "respond", "search_similar", "coach_feedback", "metrics"]
                }
            },
            "components": {
                "seeya": {
                    "name": "SmartBrief Summarizer",
                    "base_url": "http://127.0.0.1:8000",
                    "health_endpoint": "/health",
                    "enabled": True,
                    "priority": 1
                },
                "sankalp": {
                    "name": "Cognitive Agent Task Processor", 
                    "base_url": "http://127.0.0.1:8000",
                    "health_endpoint": "/health",
                    "enabled": True,
                    "priority": 2
                },
                "noopur": {
                    "name": "Response Agent",
                    "base_url": "http://127.0.0.1:8000",
                    "health_endpoint": "/health",
                    "enabled": True,
                    "priority": 3
                }
            }
        }
    
    def _setup_http_session(self) -> requests.Session:
        """Setup HTTP session with simple configuration"""
        session = requests.Session()
        # Simple session without complex retry logic for compatibility
        return session
    
    def execute_pipeline(
        self, 
        input_data: Dict[str, Any], 
        mode: PipelineMode = PipelineMode.FULL,
        execution_id: Optional[str] = None
    ) -> PipelineExecution:
        """Execute the complete pipeline synchronously"""
        
        if execution_id is None:
            execution_id = f"exec_{int(time.time() * 1000)}"
        
        execution = PipelineExecution(
            execution_id=execution_id,
            mode=mode,
            status=StepStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
        
        try:
            # Get step sequence based on mode
            step_sequence = self._get_step_sequence(mode)
            
            # Execute steps in sequence
            current_data = input_data.copy()
            
            for step_name in step_sequence:
                step_config = self._get_step_config(step_name)
                if not step_config or not step_config.get("enabled", True):
                    continue
                
                step = PipelineStep(
                    name=step_name,
                    component=step_config["component"],
                    status=StepStatus.IN_PROGRESS,
                    start_time=datetime.now(),
                    input_data=current_data.copy()
                )
                
                execution.steps.append(step)
                
                try:
                    # Execute step with retry logic
                    step_result = self._execute_step_with_retry(step_config, current_data)
                    
                    step.output_data = step_result
                    step.status = StepStatus.COMPLETED
                    step.end_time = datetime.now()
                    step.duration_ms = (step.end_time - step.start_time).total_seconds() * 1000
                    
                    # Update current_data with step output for next step
                    current_data.update(step_result)
                    
                except Exception as e:
                    step.error = str(e)
                    step.status = StepStatus.FAILED
                    step.end_time = datetime.now()
                    step.duration_ms = (step.end_time - step.start_time).total_seconds() * 1000
                    
                    # For demo purposes, continue with mock data
                    if step_name == "summarize":
                        current_data.update({
                            "summary_id": f"sum_{execution_id}",
                            "summary": f"Mock summary: {input_data.get('message_text', '')[:50]}...",
                            "intent": "info",
                            "urgency": "medium",
                            "type": "general"
                        })
                    elif step_name == "process_summary":
                        current_data.update({
                            "task_id": f"task_{execution_id}",
                            "task_summary": "Mock task created",
                            "priority": "medium",
                            "status": "pending"
                        })
                    elif step_name == "respond":
                        current_data.update({
                            "response_id": f"resp_{execution_id}",
                            "response_text": "Mock response generated",
                            "tone": "neutral",
                            "status": "ok"
                        })
            
            execution.status = StepStatus.COMPLETED
            
        except Exception as e:
            execution.status = StepStatus.FAILED
            execution.error = str(e)
        
        finally:
            execution.end_time = datetime.now()
            execution.total_duration_ms = (execution.end_time - execution.start_time).total_seconds() * 1000
            self.execution_history.append(execution)
        
        return execution
    
    def _execute_step_with_retry(self, step_config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step with retry logic"""
        retry_count = step_config.get("retry_count", 1)
        last_exception = None
        
        for attempt in range(retry_count + 1):
            try:
                result = self._execute_single_step(step_config, data)
                return result
            except Exception as e:
                last_exception = e
                if attempt < retry_count:
                    time.sleep(1)  # Simple delay
                    continue
        
        raise last_exception
    
    def _execute_single_step(self, step_config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single pipeline step"""
        component_config = self.config["components"][step_config["component"]]
        url = f"{component_config['base_url']}{step_config['endpoint']}"
        
        # Validate required fields
        required_fields = step_config.get("required_fields", [])
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Prepare request data
        request_data = {field: data[field] for field in required_fields if field in data}
        
        # Add optional fields that are present
        for key, value in data.items():
            if key not in request_data:
                request_data[key] = value
        
        timeout = step_config.get("timeout", 30)
        
        # Make HTTP request
        response = self.session.post(url, json=request_data, timeout=timeout)
        response.raise_for_status()
        
        result = response.json()
        return result
    
    def _get_step_sequence(self, mode: PipelineMode) -> List[str]:
        """Get step sequence based on pipeline mode"""
        mode_config = self.config["routing"]["bypass_modes"]
        return mode_config.get(mode.value, self.config["routing"]["default_flow"])
    
    def _get_step_config(self, step_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific step"""
        for step in self.config["sequence"]["steps"]:
            if step["name"] == step_name:
                return step
        return None
    
    def get_component_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all components"""
        health_status = {}
        
        for component_name, component_config in self.config["components"].items():
            if not component_config.get("enabled", True):
                health_status[component_name] = {
                    "status": "disabled",
                    "healthy": False
                }
                continue
            
            try:
                url = f"{component_config['base_url']}{component_config['health_endpoint']}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    health_status[component_name] = {
                        "status": "healthy",
                        "healthy": True,
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                        "details": response.json() if response.content else {}
                    }
                else:
                    health_status[component_name] = {
                        "status": f"unhealthy (HTTP {response.status_code})",
                        "healthy": False
                    }
                    
            except Exception as e:
                health_status[component_name] = {
                    "status": f"unreachable ({str(e)})",
                    "healthy": False
                }
        
        return health_status
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        recent_executions = sorted(
            self.execution_history, 
            key=lambda x: x.start_time, 
            reverse=True
        )[:limit]
        
        return [asdict(execution) for execution in recent_executions]
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get pipeline performance metrics"""
        if not self.execution_history:
            return {"total_executions": 0}
        
        successful = [e for e in self.execution_history if e.status == StepStatus.COMPLETED]
        failed = [e for e in self.execution_history if e.status == StepStatus.FAILED]
        
        avg_duration = sum(e.total_duration_ms or 0 for e in successful) / len(successful) if successful else 0
        success_rate = len(successful) / len(self.execution_history) * 100 if self.execution_history else 0
        
        return {
            "total_executions": len(self.execution_history),
            "successful_executions": len(successful),
            "failed_executions": len(failed),
            "success_rate_percent": round(success_rate, 2),
            "avg_duration_ms": round(avg_duration, 2),
            "last_execution": self.execution_history[-1].start_time.isoformat() if self.execution_history else None
        }


# Global orchestrator instance
orchestrator = None

def get_orchestrator() -> SimplePipelineOrchestrator:
    """Get or create global orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        orchestrator = SimplePipelineOrchestrator()
    return orchestrator