# src/metrics_collector.py
import json
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and stores test metrics"""
    
    def __init__(self, results_dir: str = "results"):
        self.metrics: List[Dict] = []
        self.test_timers: Dict[str, datetime] = {}
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
    def start_test(self, test_id: str, test_type: str = "unknown", test_name: str = "") -> str:
        """Start timing a test and return timer ID"""
        timer_id = f"{test_id}_{uuid.uuid4().hex[:8]}"
        self.test_timers[timer_id] = {
            "start_time": datetime.now(),
            "test_id": test_id,
            "test_type": test_type,
            "test_name": test_name
        }
        return timer_id
    
   # In src/metrics_collector.py
    def end_test(self, timer_id: str, status: str = "passed", score: float = 1.0, 
                 details: Dict = None) -> bool:
        """End a test and record its metrics"""
        try:
            if timer_id not in self.test_timers:
                logger.error(f"Timer ID {timer_id} not found")
                return False
                
            timer_data = self.test_timers[timer_id]
            start_time = timer_data["start_time"]
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            test_metric = {
                "test_id": timer_data["test_id"],
                "test_type": timer_data.get("test_type", "unknown"),
                "test_name": timer_data.get("test_name", ""),
                "status": status,
                "score": score,
                "duration_ms": duration_ms,
                "timestamp": end_time.isoformat(),
                "details": details or {}
            }
            
            self.metrics.append(test_metric)
            
            logger.info(
                f"Test Metric: {test_metric['test_type']}/{test_metric['test_name']} - "
                f"Status: {status}, Score: {score:.2f}, Duration: {duration_ms:.0f}ms"
            )
            
            del self.test_timers[timer_id]
            self._save_metrics()
            return True
            
        except Exception as e:
            logger.error(f"Error ending test {timer_id}: {str(e)}")
            return False
        
    def record_test(self, test_id: str, test_type: str, test_name: str, 
                    status: str = "passed", score: float = 1.0, 
                    duration_ms: float = 0, details: Dict = None) -> bool:
        """Record a test without using timer"""
        try:
            test_metric = {
                "test_id": test_id,
                "test_type": test_type,
                "test_name": test_name,
                "status": status,
                "score": score,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat(),
                "details": details or {}
            }
            
            self.metrics.append(test_metric)
            
            logger.info(
                f"Test Metric: {test_type}/{test_name} - "
                f"Status: {status}, Score: {score:.2f}, Duration: {duration_ms:.0f}ms"
            )
            
            self._save_metrics()
            return True
        except Exception as e:
            logger.error(f"Error recording test {test_id}: {str(e)}")
            return False
    
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
    
    def _save_metrics(self):
        """Save metrics to JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.results_dir / f"test_session_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
            
            logger.info(f"Metrics saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving metrics: {str(e)}")
    
    def clear_metrics(self):
        """Clear current session metrics"""
        self.metrics.clear()
        self.test_timers.clear()
        logger.info("Metrics cleared")