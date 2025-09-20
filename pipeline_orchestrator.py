import os
import json
import time
import asyncio
import logging
import logging.handlers
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

import requests
# import aiohttp  # Commented out for now
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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


class PipelineOrchestrator:
    """
    Complete pipeline orchestrator for AI Assistant components.
    Handles routing: Seeya → Sankalp → Noopur → Chandresh → Parth → Nilesh
    """
    
    def __init__(self, config_path: str = "pipeline_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.session = self._setup_http_session()
        self.execution_history: List[PipelineExecution] = []
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        
        # Initialize circuit breakers
        for component in self.config["components"]:
            self.circuit_breakers[component] = {
                "failures": 0,
                "last_failure": None,
                "state": "closed"  # closed, open, half-open
            }
        
        self.logger.info("Pipeline Orchestrator initialized successfully")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Pipeline config not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging system"""
        logger = logging.getLogger("PipelineOrchestrator")
        logger.setLevel(getattr(logging, self.config["logging"]["level"]))
        
        # Clear existing handlers
        logger.handlers = []
        
        formatter = logging.Formatter(self.config["logging"]["format"])
        
        # Console handler
        if self.config["logging"]["console_output"]:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler
        log_file = self.config["logging"]["file"]
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config["logging"]["max_size_mb"] * 1024 * 1024,
            backupCount=self.config["logging"]["backup_count"]
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _setup_http_session(self) -> requests.Session:
        """Setup HTTP session with retry logic"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    async def execute_pipeline(
        self, 
        input_data: Dict[str, Any], 
        mode: PipelineMode = PipelineMode.FULL,
        execution_id: Optional[str] = None
    ) -> PipelineExecution:
        """Execute the complete pipeline with specified mode"""
        
        if execution_id is None:
            execution_id = f"exec_{int(time.time() * 1000)}"
        
        execution = PipelineExecution(
            execution_id=execution_id,
            mode=mode,
            status=StepStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
        
        self.logger.info(f"Starting pipeline execution {execution_id} in {mode.value} mode")
        
        try:
            # Get step sequence based on mode
            step_sequence = self._get_step_sequence(mode)
            
            # Execute steps in sequence
            current_data = input_data.copy()
            
            for step_name in step_sequence:
                step_config = self._get_step_config(step_name)
                if not step_config["enabled"]:
                    self.logger.info(f"Skipping disabled step: {step_name}")
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
                    step_result = await self._execute_step_with_retry(step_config, current_data)
                    
                    step.output_data = step_result
                    step.status = StepStatus.COMPLETED
                    step.end_time = datetime.now()
                    step.duration_ms = (step.end_time - step.start_time).total_seconds() * 1000
                    
                    # Update current_data with step output for next step
                    current_data.update(step_result)
                    
                    self.logger.info(f"Step {step_name} completed successfully in {step.duration_ms:.2f}ms")
                    
                except Exception as e:
                    step.error = str(e)
                    step.status = StepStatus.FAILED
                    step.end_time = datetime.now()
                    step.duration_ms = (step.end_time - step.start_time).total_seconds() * 1000
                    
                    self.logger.error(f"Step {step_name} failed: {e}")
                    
                    # Handle critical vs non-critical failures
                    if step_name in self.config["routing"]["default_flow"]:
                        # Critical step failed, use fallback or fail pipeline
                        fallback_data = self._get_fallback_data(step_name)
                        if fallback_data:
                            current_data.update(fallback_data)
                            self.logger.warning(f"Using fallback data for critical step {step_name}")
                        else:
                            execution.status = StepStatus.FAILED
                            execution.error = f"Critical step {step_name} failed: {e}"
                            break
                    else:
                        # Non-critical step, continue pipeline
                        self.logger.warning(f"Non-critical step {step_name} failed, continuing pipeline")
            
            if execution.status != StepStatus.FAILED:
                execution.status = StepStatus.COMPLETED
                self.logger.info(f"Pipeline execution {execution_id} completed successfully")
            
        except Exception as e:
            execution.status = StepStatus.FAILED
            execution.error = str(e)
            self.logger.error(f"Pipeline execution {execution_id} failed: {e}")
            self.logger.error(traceback.format_exc())
        
        finally:
            execution.end_time = datetime.now()
            execution.total_duration_ms = (execution.end_time - execution.start_time).total_seconds() * 1000
            self.execution_history.append(execution)
            self._save_execution_log(execution)
        
        return execution
    
    async def _execute_step_with_retry(self, step_config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step with retry logic and circuit breaker"""
        component = step_config["component"]
        
        # Check circuit breaker
        if self._is_circuit_open(component):
            raise Exception(f"Circuit breaker open for component {component}")
        
        retry_count = step_config.get("retry_count", 1)
        retry_delays = self.config["error_handling"]["retry_delays"]
        
        last_exception = None
        
        for attempt in range(retry_count + 1):
            try:
                result = await self._execute_single_step(step_config, data)
                
                # Reset circuit breaker on success
                self._reset_circuit_breaker(component)
                
                return result
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Step {step_config['name']} attempt {attempt + 1} failed: {e}")
                
                if attempt < retry_count:
                    delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                    self.logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    # Record failure in circuit breaker
                    self._record_failure(component)
        
        raise last_exception
    
    async def _execute_single_step(self, step_config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single pipeline step using requests (sync)"""
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
        
        self.logger.debug(f"Calling {url} with data: {request_data}")
        
        # Make HTTP request using requests (sync)
        response = self.session.post(url, json=request_data, timeout=timeout)
        response.raise_for_status()
        
        result = response.json()
        self.logger.debug(f"Step result: {result}")
        
        return result
    
    def _get_step_sequence(self, mode: PipelineMode) -> List[str]:
        """Get step sequence based on pipeline mode"""
        mode_config = self.config["routing"]["bypass_modes"]
        return mode_config.get(mode.value, self.config["routing"]["default_flow"])
    
    def _get_step_config(self, step_name: str) -> Dict[str, Any]:
        """Get configuration for a specific step"""
        for step in self.config["sequence"]["steps"]:
            if step["name"] == step_name:
                return step
        raise ValueError(f"Step configuration not found: {step_name}")
    
    def _get_fallback_data(self, step_name: str) -> Optional[Dict[str, Any]]:
        """Get fallback data for failed steps"""
        fallbacks = self.config["error_handling"].get("fallback_responses", {})
        return fallbacks.get(step_name)
    
    def _is_circuit_open(self, component: str) -> bool:
        """Check if circuit breaker is open for component"""
        if not self.config["error_handling"]["circuit_breaker"]["enabled"]:
            return False
        
        breaker = self.circuit_breakers[component]
        
        if breaker["state"] == "open":
            recovery_timeout = self.config["error_handling"]["circuit_breaker"]["recovery_timeout"]
            if breaker["last_failure"] and time.time() - breaker["last_failure"] > recovery_timeout:
                breaker["state"] = "half-open"
                self.logger.info(f"Circuit breaker for {component} moved to half-open state")
                return False
            return True
        
        return False
    
    def _record_failure(self, component: str):
        """Record failure for circuit breaker"""
        breaker = self.circuit_breakers[component]
        breaker["failures"] += 1
        breaker["last_failure"] = time.time()
        
        failure_threshold = self.config["error_handling"]["circuit_breaker"]["failure_threshold"]
        if breaker["failures"] >= failure_threshold:
            breaker["state"] = "open"
            self.logger.warning(f"Circuit breaker opened for component {component}")
    
    def _reset_circuit_breaker(self, component: str):
        """Reset circuit breaker on successful execution"""
        breaker = self.circuit_breakers[component]
        breaker["failures"] = 0
        breaker["state"] = "closed"
    
    def _save_execution_log(self, execution: PipelineExecution):
        """Save execution log to file"""
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        log_file = logs_dir / f"execution_{execution.execution_id}.json"
        
        try:
            with open(log_file, 'w') as f:
                json.dump(asdict(execution), f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save execution log: {e}")
    
    def get_component_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all components"""
        health_status = {}
        
        for component_name, component_config in self.config["components"].items():
            if not component_config["enabled"]:
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

def get_orchestrator() -> PipelineOrchestrator:
    """Get or create global orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        orchestrator = PipelineOrchestrator()
    return orchestrator


if __name__ == "__main__":
    # Test the orchestrator
    async def test_pipeline():
        orch = PipelineOrchestrator()
        
        test_input = {
            "user_id": "test_user",
            "platform": "email",
            "message_text": "Can we schedule a meeting for tomorrow at 2pm?",
            "timestamp": datetime.now().isoformat()
        }
        
        execution = await orch.execute_pipeline(test_input, PipelineMode.QUICK)
        print(f"Execution completed with status: {execution.status}")
        print(f"Total duration: {execution.total_duration_ms}ms")
        
        for step in execution.steps:
            print(f"Step {step.name}: {step.status} ({step.duration_ms}ms)")
    
    asyncio.run(test_pipeline())