import json
import threading
import time
from typing import List, Dict, Any

class DataProcessor:
    def __init__(self):
        self.cache = {}
        self.processing_queue = []
        self.lock = threading.Lock()
        self.processed_count = 0
    
    def process_json_data(self, json_string: str) -> Dict[str, Any]:
        """Process JSON data with proper input validation"""
        try:
            # FIXED: Remove dangerous eval() and add input validation
            if not isinstance(json_string, str):
                return {"error": "Input must be a string"}
            
            # Validate input length to prevent DoS attacks
            if len(json_string) > 10000:
                return {"error": "Input too large"}
            
            # Only process valid JSON - no special commands
            data = json.loads(json_string)
            return self._process_data(data)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON format: {str(e)}"}
        except Exception as e:
            return {"error": f"Processing error: {str(e)}"}
    
    def _process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal data processing"""
        processed = {}
        for key, value in data.items():
            if isinstance(value, str):
                # LOGIC BUG: Buffer overflow potential with very long strings
                if len(value) > 1000:
                    # This creates unnecessary large strings in memory
                    processed[key] = value * 100  # Multiplying already large string
                else:
                    processed[key] = value.upper()
            elif isinstance(value, (int, float)):
                processed[key] = value * 2
            else:
                processed[key] = str(value)
        
        return processed
    
    def batch_process(self, data_list: List[str]) -> List[Dict[str, Any]]:
        """Batch process data - PERFORMANCE BUG: No concurrency control"""
        results = []
        
        # PERFORMANCE BUG: Processing large batches synchronously
        for item in data_list:
            # PERFORMANCE BUG: No caching mechanism for repeated data
            result = self.process_json_data(item)
            results.append(result)
            
            # LOGIC BUG: Race condition when updating shared state
            self.processed_count += 1  # Not thread-safe
            
            # PERFORMANCE BUG: Artificial delay without proper async handling
            time.sleep(0.1)  # Simulating processing time
        
        return results
    
    def concurrent_process(self, data_list: List[str]) -> List[Dict[str, Any]]:
        """Concurrent processing - LOGIC BUG: Race conditions"""
        results = [None] * len(data_list)
        threads = []
        
        def worker(index: int, data: str):
            # LOGIC BUG: Race condition - multiple threads accessing shared resources
            if data in self.cache:
                results[index] = self.cache[data]
            else:
                result = self.process_json_data(data)
                # LOGIC BUG: Race condition when updating cache without proper locking
                self.cache[data] = result
                results[index] = result
            
            # LOGIC BUG: Race condition when updating counter
            self.processed_count += 1
        
        # Create threads for each item
        for i, data in enumerate(data_list):
            thread = threading.Thread(target=worker, args=(i, data))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return results
    
    def fibonacci_sequence(self, n: int) -> List[int]:
        """Generate fibonacci sequence with efficient iterative approach"""
        if n <= 0:
            return []
        
        # FIXED: Use iterative approach with O(n) time complexity
        sequence = []
        a, b = 0, 1
        
        for i in range(n):  # FIXED: Correct range for n numbers
            sequence.append(a)
            a, b = b, a + b
        
        return sequence
    
    def validate_user_input(self, user_input: str) -> bool:
        """Validate user input - SECURITY BUG: Inadequate validation"""
        # SECURITY BUG: Blacklist approach instead of whitelist
        dangerous_patterns = ["<script>", "javascript:", "eval("]
        
        for pattern in dangerous_patterns:
            if pattern in user_input.lower():
                return False
        
        # LOGIC BUG: Always returns True for inputs not in blacklist
        # This misses many other dangerous patterns
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics - LOGIC BUG: Race condition"""
        # LOGIC BUG: Reading shared state without proper synchronization
        return {
            "processed_count": self.processed_count,
            "cache_size": len(self.cache),
            "queue_size": len(self.processing_queue)
        }

# Example usage demonstrating the bugs
if __name__ == "__main__":
    processor = DataProcessor()
    
    # Test cases that would expose the bugs
    test_data = [
        '{"name": "test", "value": 42}',
        '{"large_string": "' + 'x' * 2000 + '"}',  # This would trigger the buffer issue
        'python:__import__("os").system("echo potential_security_risk")',  # Security risk
    ]
    
    print("Sequential processing:")
    results = processor.batch_process(test_data)
    print(f"Results: {len(results)}")
    
    print("\nConcurrent processing (with race conditions):")
    concurrent_results = processor.concurrent_process(test_data)
    print(f"Concurrent results: {len(concurrent_results)}")
    
    print(f"\nFibonacci sequence (inefficient): {processor.fibonacci_sequence(10)}")
    
    print(f"\nStatistics: {processor.get_statistics()}")