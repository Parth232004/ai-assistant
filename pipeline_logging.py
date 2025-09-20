"""
Standardized logging system for AI Assistant Pipeline
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


class PipelineLogger:
    """Centralized logging for AI Assistant Pipeline"""
    
    def __init__(self, config_path: str = "pipeline_config.json"):
        self.config = self._load_config(config_path)
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self._setup_loggers()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r') as f:
                return json.load(f).get("logging", {})
        except Exception:
            return {
                "level": "INFO",
                "console_output": True,
                "file": "logs/pipeline.log"
            }
    
    def _setup_loggers(self):
        """Setup structured loggers"""
        self.loggers = {}
        
        # Main pipeline logger
        self.pipeline_logger = self._create_logger("pipeline", "pipeline.log")
        
        # Component loggers
        components = ["seeya", "sankalp", "noopur", "chandresh", "parth", "nilesh"]
        for component in components:
            self.loggers[component] = self._create_logger(component, f"{component}.log")
    
    def _create_logger(self, name: str, log_file: str) -> logging.Logger:
        """Create a configured logger"""
        logger = logging.getLogger(f"ai_assistant.{name}")
        logger.setLevel(getattr(logging, self.config.get("level", "INFO")))
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(self.logs_dir / log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        if self.config.get("console_output", True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def log_execution_start(self, execution_id: str, mode: str, input_data: Dict[str, Any]):
        """Log pipeline execution start"""
        self.pipeline_logger.info(f"EXECUTION_START | ID: {execution_id} | Mode: {mode}")
        
        # Save detailed log
        self._save_structured_log({
            "type": "execution_start",
            "execution_id": execution_id,
            "mode": mode,
            "timestamp": datetime.now().isoformat(),
            "input_data": input_data
        })
    
    def log_execution_end(self, execution_id: str, status: str, duration_ms: float):
        """Log pipeline execution end"""
        self.pipeline_logger.info(f"EXECUTION_END | ID: {execution_id} | Status: {status} | Duration: {duration_ms:.2f}ms")
        
        self._save_structured_log({
            "type": "execution_end",
            "execution_id": execution_id,
            "status": status,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_step_start(self, execution_id: str, step_name: str, component: str):
        """Log step start"""
        logger = self.loggers.get(component, self.pipeline_logger)
        logger.info(f"STEP_START | Execution: {execution_id} | Step: {step_name}")
    
    def log_step_end(self, execution_id: str, step_name: str, component: str, status: str, duration_ms: float):
        """Log step end"""
        logger = self.loggers.get(component, self.pipeline_logger)
        logger.info(f"STEP_END | Execution: {execution_id} | Step: {step_name} | Status: {status} | Duration: {duration_ms:.2f}ms")
    
    def log_error(self, execution_id: str, component: str, error: str, step_name: Optional[str] = None):
        """Log error"""
        logger = self.loggers.get(component, self.pipeline_logger)
        context = f"Step: {step_name} | " if step_name else ""
        logger.error(f"ERROR | Execution: {execution_id} | {context}Component: {component} | Error: {error}")
        
        self._save_structured_log({
            "type": "error",
            "execution_id": execution_id,
            "component": component,
            "step_name": step_name,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def _save_structured_log(self, log_data: Dict[str, Any]):
        """Save structured log entry"""
        log_file = self.logs_dir / "structured_logs.jsonl"
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_data) + '\n')
        except Exception as e:
            self.pipeline_logger.error(f"Failed to save structured log: {e}")
    
    def get_recent_logs(self, component: Optional[str] = None, limit: int = 100) -> List[str]:
        """Get recent log entries"""
        if component and component in self.loggers:
            log_file = self.logs_dir / f"{component}.log"
        else:
            log_file = self.logs_dir / "pipeline.log"
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            return lines[-limit:] if len(lines) > limit else lines
        except Exception:
            return []


# Global logger instance
pipeline_logger = None

def get_logger() -> PipelineLogger:
    """Get global logger instance"""
    global pipeline_logger
    if pipeline_logger is None:
        pipeline_logger = PipelineLogger()
    return pipeline_logger


def log_summary_data(summary_data: Dict[str, Any]):
    """Log summary creation for aggregation"""
    logger = get_logger()
    summary_file = logger.logs_dir / "log_summaries.json"
    
    # Load existing summaries
    summaries = []
    if summary_file.exists():
        try:
            with open(summary_file, 'r') as f:
                summaries = json.load(f)
        except Exception:
            summaries = []
    
    # Add new summary
    summaries.append({
        "timestamp": datetime.now().isoformat(),
        "summary_id": summary_data.get("summary_id"),
        "user_id": summary_data.get("user_id"),
        "platform": summary_data.get("platform"),
        "intent": summary_data.get("intent"),
        "urgency": summary_data.get("urgency"),
        "summary_text": summary_data.get("summary", "")[:200]  # Truncate for storage
    })
    
    # Keep only last 1000 summaries
    if len(summaries) > 1000:
        summaries = summaries[-1000:]
    
    # Save back
    try:
        with open(summary_file, 'w') as f:
            json.dump(summaries, f, indent=2)
    except Exception as e:
        logger.pipeline_logger.error(f"Failed to save summary log: {e}")


def log_task_data(task_data: Dict[str, Any]):
    """Log task creation for aggregation"""
    logger = get_logger()
    task_file = logger.logs_dir / "log_tasks.json"
    
    # Similar structure to summaries
    tasks = []
    if task_file.exists():
        try:
            with open(task_file, 'r') as f:
                tasks = json.load(f)
        except Exception:
            tasks = []
    
    tasks.append({
        "timestamp": datetime.now().isoformat(),
        "task_id": task_data.get("task_id"),
        "summary_id": task_data.get("summary_id"),
        "user_id": task_data.get("user_id"),
        "priority": task_data.get("priority"),
        "status": task_data.get("status"),
        "task_summary": task_data.get("task_summary", "")[:200]
    })
    
    if len(tasks) > 1000:
        tasks = tasks[-1000:]
    
    try:
        with open(task_file, 'w') as f:
            json.dump(tasks, f, indent=2)
    except Exception as e:
        logger.pipeline_logger.error(f"Failed to save task log: {e}")


def log_response_data(response_data: Dict[str, Any]):
    """Log response generation for aggregation"""
    logger = get_logger()
    response_file = logger.logs_dir / "log_responses.json"
    
    responses = []
    if response_file.exists():
        try:
            with open(response_file, 'r') as f:
                responses = json.load(f)
        except Exception:
            responses = []
    
    responses.append({
        "timestamp": datetime.now().isoformat(),
        "response_id": response_data.get("response_id"),
        "task_id": response_data.get("task_id"),
        "user_id": response_data.get("user_id"),
        "tone": response_data.get("tone"),
        "status": response_data.get("status"),
        "response_text": response_data.get("response_text", "")[:200]
    })
    
    if len(responses) > 1000:
        responses = responses[-1000:]
    
    try:
        with open(response_file, 'w') as f:
            json.dump(responses, f, indent=2)
    except Exception as e:
        logger.pipeline_logger.error(f"Failed to save response log: {e}")