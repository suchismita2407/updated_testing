# src/detailed_metrics_collector.py
import json
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional
import uuid
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetailedMetricsCollector:
    """Collects and stores detailed test metrics with inputs/outputs"""
    
    def __init__(self, data_dir: str = "data"):
        self.metrics: List[Dict] = []
        self.test_timers: Dict[str, Dict] = {}
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.data_dir / "test_cases").mkdir(exist_ok=True)
        (self.data_dir / "prompts").mkdir(exist_ok=True)
        (self.data_dir / "credentials").mkdir(exist_ok=True)
        (self.data_dir / "results").mkdir(exist_ok=True)
        
    def start_test(self, test_id: str, test_type: str = "unknown", 
                   test_name: str = "", inputs: Dict = None) -> str:
        """Start timing a test and store inputs"""
        timer_id = f"{test_id}_{uuid.uuid4().hex[:8]}"
        
        self.test_timers[timer_id] = {
            "start_time": datetime.now(),
            "test_id": test_id,
            "test_type": test_type,
            "test_name": test_name,
            "inputs": inputs or {},
            "timer_id": timer_id
        }
        
        # Save inputs to file
        if inputs:
            self._save_test_inputs(timer_id, test_type, test_name, inputs)
        
        return timer_id
    
    def _save_test_inputs(self, timer_id: str, test_type: str, 
                         test_name: str, inputs: Dict):
        """Save test inputs to JSON file"""
        try:
            filename = self.data_dir / "test_cases" / f"{timer_id}_inputs.json"
            data = {
                "timer_id": timer_id,
                "test_type": test_type,
                "test_name": test_name,
                "inputs": inputs,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved test inputs to {filename}")
        except Exception as e:
            logger.error(f"Error saving test inputs: {e}")
    
    def end_test(self, timer_id: str, status: str = "passed", 
                 score: float = 1.0, outputs: Dict = None, 
                 details: Dict = None, justification: str = None) -> bool:
        """End a test and record its metrics with outputs"""
        try:
            if timer_id not in self.test_timers:
                logger.error(f"Timer ID {timer_id} not found")
                return False
                
            timer_data = self.test_timers[timer_id]
            start_time = timer_data["start_time"]
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            test_metric = {
                "timer_id": timer_id,
                "test_id": timer_data["test_id"],
                "test_type": timer_data["test_type"],
                "test_name": timer_data["test_name"],
                "inputs": timer_data.get("inputs", {}),
                "status": status,
                "score": score,
                "duration_ms": duration_ms,
                "timestamp": end_time.isoformat(),
                "outputs": outputs or {},
                "details": details or {},
                "justification": justification or self._generate_justification(status, score, details),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
            self.metrics.append(test_metric)
            
            # Save detailed results
            self._save_detailed_results(test_metric)
            
            # Log the metric
            logger.info(
                f"Test Metric: {test_metric['test_type']}/{test_metric['test_name']} - "
                f"Status: {status}, Score: {score:.2f}, Duration: {duration_ms:.0f}ms"
            )
            
            # Remove timer
            del self.test_timers[timer_id]
            
            # Save to session file
            self._save_session_metrics()
            
            return True
        except Exception as e:
            logger.error(f"Error ending test {timer_id}: {str(e)}")
            return False
    
    def _generate_justification(self, status: str, score: float, details: Dict) -> str:
        """Generate justification for test result"""
        if status == "passed":
            if score >= 0.9:
                return "Excellent performance - all criteria met with high quality"
            elif score >= 0.7:
                return "Good performance - main criteria met"
            else:
                return "Passed but with room for improvement"
        elif status == "failed":
            if score == 0:
                return "Complete failure - no criteria met"
            elif score < 0.3:
                return "Poor performance - most criteria failed"
            else:
                return "Partial failure - some criteria met but not enough to pass"
        else:
            return f"Test ended with status: {status}"
    
    def _save_detailed_results(self, test_metric: Dict):
        """Save detailed test results to JSON file"""
        try:
            filename = self.data_dir / "results" / f"{test_metric['timer_id']}_results.json"
            
            with open(filename, 'w') as f:
                json.dump(test_metric, f, indent=2)
                
            logger.info(f"Saved detailed results to {filename}")
        except Exception as e:
            logger.error(f"Error saving detailed results: {e}")
    
    def _save_session_metrics(self):
        """Save current session metrics to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.data_dir / "results" / f"session_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
            
            logger.info(f"Session metrics saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving session metrics: {e}")
    
    def save_prompts(self, prompts: List[Dict], filename: str = None):
        """Save generated prompts to file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"prompts_{timestamp}.json"
            
            filepath = self.data_dir / "prompts" / filename
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "total_prompts": len(prompts),
                "prompts": prompts
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(prompts)} prompts to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving prompts: {e}")
            return None
    
    def save_credentials(self, credentials: List[Dict], filename: str = None):
        """Save test credentials to file"""
        try:
            if not filename:
                filename = "test_credentials.json"
            
            filepath = self.data_dir / "credentials" / filename
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "total_credentials": len(credentials),
                "credentials": credentials
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(credentials)} credentials to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            return None
    
    def get_test_details(self, timer_id: str) -> Optional[Dict]:
        """Get detailed test information by timer ID"""
        for metric in self.metrics:
            if metric.get("timer_id") == timer_id:
                return metric
        return None
    
    def get_tests_by_type(self, test_type: str) -> List[Dict]:
        """Get all tests of a specific type"""
        return [m for m in self.metrics if m.get("test_type") == test_type]
    
    def get_failed_tests(self) -> List[Dict]:
        """Get all failed tests"""
        return [m for m in self.metrics if m.get("status") == "failed"]
    
    def get_session_metrics(self) -> List[Dict]:
        """Get all metrics from current session"""
        return self.metrics.copy()
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        if not self.metrics:
            return {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "success_rate": 0,
                "avg_score": 0,
                "avg_duration_ms": 0,
                "by_type": {}
            }
        
        total_tests = len(self.metrics)
        passed_tests = sum(1 for m in self.metrics if m["status"] == "passed")
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        avg_score = sum(m["score"] for m in self.metrics) / total_tests if total_tests > 0 else 0
        avg_duration = sum(m["duration_ms"] for m in self.metrics) / total_tests if total_tests > 0 else 0
        
        # Group by type
        by_type = {}
        for metric in self.metrics:
            test_type = metric["test_type"]
            if test_type not in by_type:
                by_type[test_type] = []
            by_type[test_type].append(metric)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "avg_score": avg_score,
            "avg_duration_ms": avg_duration,
            "by_type": by_type
        }
    
    def export_to_csv(self, filename: str = None):
        """Export metrics to CSV"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"test_metrics_{timestamp}.csv"
            
            filepath = self.data_dir / filename
            
            # Flatten the data for CSV
            flat_data = []
            for metric in self.metrics:
                flat_metric = {
                    "timer_id": metric.get("timer_id"),
                    "test_id": metric.get("test_id"),
                    "test_type": metric.get("test_type"),
                    "test_name": metric.get("test_name"),
                    "status": metric.get("status"),
                    "score": metric.get("score"),
                    "duration_ms": metric.get("duration_ms"),
                    "timestamp": metric.get("timestamp"),
                    "justification": metric.get("justification", ""),
                    "start_time": metric.get("start_time"),
                    "end_time": metric.get("end_time")
                }
                
                # Add inputs as separate columns
                inputs = metric.get("inputs", {})
                for key, value in inputs.items():
                    if isinstance(value, (str, int, float, bool)):
                        flat_metric[f"input_{key}"] = str(value)
                    elif isinstance(value, dict):
                        flat_metric[f"input_{key}"] = json.dumps(value)
                    else:
                        flat_metric[f"input_{key}"] = str(value)
                
                flat_data.append(flat_metric)
            
            df = pd.DataFrame(flat_data)
            df.to_csv(filepath, index=False)
            
            logger.info(f"Exported metrics to CSV: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
    
    def clear_metrics(self):
        """Clear current session metrics"""
        self.metrics.clear()
        self.test_timers.clear()
        logger.info("Metrics cleared")