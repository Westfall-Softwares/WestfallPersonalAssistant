#!/usr/bin/env python3
"""
Local AI Optimization and Personalization Module
Handles AI model optimization, resource management, personalization, and local processing
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
import psutil
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)


class AIModelOptimizer(QObject):
    """Optimizes AI models for better performance and lower memory usage"""
    
    optimization_completed = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.optimization_cache = {}
        self.model_profiles = {}
        self.load_optimization_cache()
        
    def optimize_model_for_system(self, model_path: str, system_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize model configuration for current system"""
        optimization_key = f"{model_path}_{hash(str(system_specs))}"
        
        # Check cache first
        if optimization_key in self.optimization_cache:
            cached_result = self.optimization_cache[optimization_key]
            # Check if cache is still valid (within 24 hours)
            cache_time = datetime.fromisoformat(cached_result.get('timestamp', ''))
            if datetime.now() - cache_time < timedelta(hours=24):
                return cached_result['config']
        
        # Calculate optimal configuration
        config = self._calculate_optimal_config(model_path, system_specs)
        
        # Cache the result
        self.optimization_cache[optimization_key] = {
            'config': config,
            'timestamp': datetime.now().isoformat(),
            'system_specs': system_specs
        }
        self.save_optimization_cache()
        
        self.optimization_completed.emit('model_optimized', config)
        return config
    
    def _calculate_optimal_config(self, model_path: str, system_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal configuration based on system specifications"""
        config = {
            'use_gpu': False,
            'gpu_layers': 0,
            'context_length': 2048,
            'batch_size': 1,
            'threads': 4,
            'memory_limit_mb': 2048,
            'quantization': 'auto',
            'precision': 'fp32'
        }
        
        # Get system info
        total_memory_gb = system_specs.get('total_memory_gb', 8)
        cpu_cores = system_specs.get('cpu_cores', 4)
        gpu_memory_gb = system_specs.get('gpu_memory_gb', 0)
        gpu_available = system_specs.get('gpu_available', False)
        
        # Optimize for available memory
        if total_memory_gb >= 16:
            config.update({
                'context_length': 4096,
                'memory_limit_mb': min(6144, int(total_memory_gb * 1024 * 0.4)),
                'batch_size': 2
            })
        elif total_memory_gb >= 8:
            config.update({
                'context_length': 2048,
                'memory_limit_mb': min(3072, int(total_memory_gb * 1024 * 0.3)),
                'batch_size': 1
            })
        else:
            config.update({
                'context_length': 1024,
                'memory_limit_mb': min(2048, int(total_memory_gb * 1024 * 0.25)),
                'batch_size': 1
            })
        
        # Optimize for CPU
        config['threads'] = min(cpu_cores, 8)  # Don't use all cores
        
        # GPU optimization
        if gpu_available and gpu_memory_gb > 0:
            config['use_gpu'] = True
            
            if gpu_memory_gb >= 8:
                config.update({
                    'gpu_layers': 35,
                    'precision': 'fp16',
                    'quantization': 'q4_1'
                })
            elif gpu_memory_gb >= 6:
                config.update({
                    'gpu_layers': 25,
                    'precision': 'fp16',
                    'quantization': 'q4_1'
                })
            elif gpu_memory_gb >= 4:
                config.update({
                    'gpu_layers': 15,
                    'precision': 'int8',
                    'quantization': 'q8_0'
                })
            else:
                config.update({
                    'gpu_layers': 5,
                    'precision': 'int8',
                    'quantization': 'q8_0'
                })
        
        # Model-specific optimizations
        model_size_gb = self._estimate_model_size(model_path)
        if model_size_gb > 7:  # Large model
            config['quantization'] = 'q4_1' if config['quantization'] == 'auto' else config['quantization']
        elif model_size_gb > 3:  # Medium model
            config['quantization'] = 'q5_1' if config['quantization'] == 'auto' else config['quantization']
        else:  # Small model
            config['quantization'] = 'q8_0' if config['quantization'] == 'auto' else config['quantization']
        
        return config
    
    def _estimate_model_size(self, model_path: str) -> float:
        """Estimate model size in GB"""
        try:
            if os.path.exists(model_path):
                size_bytes = os.path.getsize(model_path)
                return size_bytes / (1024**3)
        except:
            pass
        return 3.0  # Default estimate
    
    def get_model_performance_profile(self, model_path: str) -> Dict[str, Any]:
        """Get performance profile for a model"""
        if model_path in self.model_profiles:
            return self.model_profiles[model_path]
        
        # Create basic profile
        profile = {
            'model_path': model_path,
            'size_gb': self._estimate_model_size(model_path),
            'avg_tokens_per_second': 0.0,
            'avg_memory_usage_mb': 0.0,
            'load_time_seconds': 0.0,
            'last_updated': datetime.now().isoformat()
        }
        
        self.model_profiles[model_path] = profile
        return profile
    
    def update_model_performance(self, model_path: str, performance_data: Dict[str, Any]):
        """Update model performance data"""
        if model_path not in self.model_profiles:
            self.model_profiles[model_path] = self.get_model_performance_profile(model_path)
        
        profile = self.model_profiles[model_path]
        
        # Update performance metrics with weighted average
        for metric in ['avg_tokens_per_second', 'avg_memory_usage_mb', 'load_time_seconds']:
            if metric in performance_data:
                current_value = profile.get(metric, 0.0)
                new_value = performance_data[metric]
                # Use exponential moving average
                profile[metric] = current_value * 0.7 + new_value * 0.3
        
        profile['last_updated'] = datetime.now().isoformat()
        self.save_optimization_cache()
    
    def load_optimization_cache(self):
        """Load optimization cache from disk"""
        try:
            cache_file = Path.home() / '.westfall_assistant' / 'ai_optimization_cache.json'
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.optimization_cache = data.get('optimization_cache', {})
                    self.model_profiles = data.get('model_profiles', {})
                logger.info("AI optimization cache loaded")
        except Exception as e:
            logger.error(f"Failed to load optimization cache: {e}")
    
    def save_optimization_cache(self):
        """Save optimization cache to disk"""
        try:
            cache_dir = Path.home() / '.westfall_assistant'
            cache_dir.mkdir(exist_ok=True)
            cache_file = cache_dir / 'ai_optimization_cache.json'
            
            data = {
                'optimization_cache': self.optimization_cache,
                'model_profiles': self.model_profiles
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save optimization cache: {e}")


class AIModelHotSwapper(QObject):
    """Manages hot-swapping of AI models to reduce memory footprint"""
    
    model_swapped = pyqtSignal(str, str)  # old_model, new_model
    memory_freed = pyqtSignal(int)  # memory_freed_mb
    
    def __init__(self, max_loaded_models: int = 2):
        super().__init__()
        self.max_loaded_models = max_loaded_models
        self.loaded_models = {}  # model_path -> (model_object, last_used_time, memory_usage)
        self.model_queue = []  # LRU queue
        self.swap_in_progress = False
        
    def load_model(self, model_path: str, force_reload: bool = False) -> Optional[Any]:
        """Load a model with hot-swapping support"""
        if self.swap_in_progress:
            logger.warning("Model swap in progress, waiting...")
            return None
        
        # Check if model is already loaded
        if model_path in self.loaded_models and not force_reload:
            self._update_model_usage(model_path)
            return self.loaded_models[model_path][0]
        
        # Check if we need to free memory
        if len(self.loaded_models) >= self.max_loaded_models:
            self._free_least_used_model()
        
        # Load the new model
        try:
            self.swap_in_progress = True
            model_object = self._load_model_implementation(model_path)
            memory_usage = self._estimate_model_memory(model_object)
            
            self.loaded_models[model_path] = (
                model_object,
                datetime.now(),
                memory_usage
            )
            
            # Update queue
            if model_path in self.model_queue:
                self.model_queue.remove(model_path)
            self.model_queue.append(model_path)
            
            logger.info(f"Model loaded: {model_path} ({memory_usage}MB)")
            return model_object
            
        except Exception as e:
            logger.error(f"Failed to load model {model_path}: {e}")
            return None
        finally:
            self.swap_in_progress = False
    
    def unload_model(self, model_path: str) -> bool:
        """Manually unload a specific model"""
        if model_path not in self.loaded_models:
            return False
        
        try:
            model_object, _, memory_usage = self.loaded_models[model_path]
            
            # Cleanup model
            self._cleanup_model(model_object)
            
            # Remove from tracking
            del self.loaded_models[model_path]
            if model_path in self.model_queue:
                self.model_queue.remove(model_path)
            
            self.memory_freed.emit(memory_usage)
            logger.info(f"Model unloaded: {model_path} ({memory_usage}MB freed)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload model {model_path}: {e}")
            return False
    
    def _free_least_used_model(self):
        """Free the least recently used model"""
        if not self.model_queue:
            return
        
        lru_model = self.model_queue[0]
        old_model = lru_model
        
        if self.unload_model(lru_model):
            self.model_swapped.emit(old_model, "")
    
    def _update_model_usage(self, model_path: str):
        """Update model usage timestamp and queue position"""
        if model_path in self.loaded_models:
            model_object, _, memory_usage = self.loaded_models[model_path]
            self.loaded_models[model_path] = (model_object, datetime.now(), memory_usage)
            
            # Move to end of queue (most recently used)
            if model_path in self.model_queue:
                self.model_queue.remove(model_path)
            self.model_queue.append(model_path)
    
    def _load_model_implementation(self, model_path: str) -> Any:
        """Load model implementation (placeholder)"""
        # This would integrate with the actual AI model loading code
        # For now, return a mock object
        return {"model_path": model_path, "loaded_at": datetime.now()}
    
    def _estimate_model_memory(self, model_object: Any) -> int:
        """Estimate model memory usage in MB"""
        # This would calculate actual memory usage
        # For now, return a reasonable estimate
        return 1024  # 1GB default
    
    def _cleanup_model(self, model_object: Any):
        """Cleanup model resources"""
        # This would perform actual cleanup
        pass
    
    def get_memory_usage_summary(self) -> Dict[str, Any]:
        """Get summary of current memory usage"""
        total_memory = sum(memory for _, _, memory in self.loaded_models.values())
        
        return {
            'loaded_models': len(self.loaded_models),
            'total_memory_mb': total_memory,
            'models': [
                {
                    'path': path,
                    'memory_mb': memory,
                    'last_used': last_used.isoformat()
                }
                for path, (_, last_used, memory) in self.loaded_models.items()
            ]
        }


class PersonalizationEngine(QObject):
    """AI personalization based on usage patterns and preferences"""
    
    preference_learned = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.user_preferences = {}
        self.usage_patterns = {}
        self.learning_data = []
        self.db_path = Path.home() / '.westfall_assistant' / 'personalization.db'
        self._init_database()
        self.load_preferences()
        
    def _init_database(self):
        """Initialize personalization database"""
        try:
            self.db_path.parent.mkdir(exist_ok=True)
            
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        interaction_type TEXT NOT NULL,
                        context TEXT,
                        user_response TEXT,
                        feedback_score REAL
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS learned_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        preference_key TEXT UNIQUE NOT NULL,
                        preference_value TEXT NOT NULL,
                        confidence_score REAL,
                        last_updated TEXT
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS usage_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_name TEXT NOT NULL,
                        pattern_data TEXT NOT NULL,
                        frequency REAL,
                        last_seen TEXT
                    )
                ''')
                
        except Exception as e:
            logger.error(f"Failed to initialize personalization database: {e}")
    
    def record_interaction(self, interaction_type: str, context: str, 
                          user_response: str, feedback_score: float = 0.0):
        """Record user interaction for learning"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    INSERT INTO user_interactions 
                    (timestamp, interaction_type, context, user_response, feedback_score)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    interaction_type,
                    context,
                    user_response,
                    feedback_score
                ))
            
            # Trigger learning
            self._analyze_interaction(interaction_type, context, user_response, feedback_score)
            
        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")
    
    def _analyze_interaction(self, interaction_type: str, context: str, 
                           user_response: str, feedback_score: float):
        """Analyze interaction and update preferences"""
        try:
            # Extract preferences from interaction
            preferences = self._extract_preferences(interaction_type, context, user_response)
            
            for pref_key, pref_value in preferences.items():
                self._update_preference(pref_key, pref_value, feedback_score)
            
            # Update usage patterns
            self._update_usage_pattern(interaction_type, context)
            
        except Exception as e:
            logger.error(f"Failed to analyze interaction: {e}")
    
    def _extract_preferences(self, interaction_type: str, context: str, 
                           user_response: str) -> Dict[str, Any]:
        """Extract preferences from user interaction"""
        preferences = {}
        
        # Response length preference
        response_length = len(user_response.split())
        if response_length > 0:
            current_length_pref = self.user_preferences.get('preferred_response_length', 50)
            # Adjust preference towards actual response length
            new_length_pref = (current_length_pref * 0.8) + (response_length * 0.2)
            preferences['preferred_response_length'] = new_length_pref
        
        # Formality preference
        if self._detect_formal_language(user_response):
            preferences['communication_style'] = 'formal'
        elif self._detect_casual_language(user_response):
            preferences['communication_style'] = 'casual'
        
        # Topic preferences
        topics = self._extract_topics(context, user_response)
        for topic in topics:
            pref_key = f'topic_interest_{topic}'
            current_interest = self.user_preferences.get(pref_key, 0.5)
            preferences[pref_key] = min(1.0, current_interest + 0.1)
        
        return preferences
    
    def _detect_formal_language(self, text: str) -> bool:
        """Detect formal language patterns"""
        formal_indicators = [
            'please', 'thank you', 'would you', 'could you',
            'i would appreciate', 'kindly', 'respectfully'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in formal_indicators)
    
    def _detect_casual_language(self, text: str) -> bool:
        """Detect casual language patterns"""
        casual_indicators = [
            'thanks', 'thx', 'hey', 'hi', 'cool', 'awesome',
            'yeah', 'yep', 'ok', 'okay', 'btw', 'lol'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in casual_indicators)
    
    def _extract_topics(self, context: str, response: str) -> List[str]:
        """Extract topics from context and response"""
        # Simple keyword-based topic extraction
        topics = []
        combined_text = f"{context} {response}".lower()
        
        topic_keywords = {
            'programming': ['code', 'programming', 'software', 'algorithm', 'debug'],
            'business': ['business', 'meeting', 'project', 'deadline', 'client'],
            'personal': ['personal', 'family', 'hobby', 'leisure', 'vacation'],
            'technical': ['technical', 'system', 'server', 'database', 'network'],
            'creative': ['creative', 'design', 'art', 'writing', 'music']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _update_preference(self, pref_key: str, pref_value: Any, confidence: float):
        """Update a learned preference"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Check if preference exists
                cursor = conn.execute(
                    'SELECT preference_value, confidence_score FROM learned_preferences WHERE preference_key = ?',
                    (pref_key,)
                )
                result = cursor.fetchone()
                
                if result:
                    # Update existing preference
                    current_value, current_confidence = result
                    
                    # Weighted average based on confidence
                    if isinstance(pref_value, (int, float)):
                        try:
                            current_numeric = float(current_value)
                            new_value = (current_numeric * current_confidence + pref_value * confidence) / (current_confidence + confidence)
                        except:
                            new_value = pref_value
                    else:
                        new_value = pref_value
                    
                    new_confidence = min(1.0, current_confidence + confidence * 0.1)
                    
                    conn.execute('''
                        UPDATE learned_preferences 
                        SET preference_value = ?, confidence_score = ?, last_updated = ?
                        WHERE preference_key = ?
                    ''', (str(new_value), new_confidence, datetime.now().isoformat(), pref_key))
                else:
                    # Insert new preference
                    conn.execute('''
                        INSERT INTO learned_preferences 
                        (preference_key, preference_value, confidence_score, last_updated)
                        VALUES (?, ?, ?, ?)
                    ''', (pref_key, str(pref_value), confidence, datetime.now().isoformat()))
                
                # Update in-memory cache
                self.user_preferences[pref_key] = pref_value
                
                self.preference_learned.emit(pref_key, {
                    'value': pref_value,
                    'confidence': confidence
                })
                
        except Exception as e:
            logger.error(f"Failed to update preference {pref_key}: {e}")
    
    def _update_usage_pattern(self, interaction_type: str, context: str):
        """Update usage patterns"""
        pattern_name = f"{interaction_type}_{hash(context) % 1000}"
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Check if pattern exists
                cursor = conn.execute(
                    'SELECT frequency FROM usage_patterns WHERE pattern_name = ?',
                    (pattern_name,)
                )
                result = cursor.fetchone()
                
                if result:
                    # Update frequency
                    current_frequency = result[0]
                    new_frequency = min(1.0, current_frequency + 0.05)
                    
                    conn.execute('''
                        UPDATE usage_patterns 
                        SET frequency = ?, last_seen = ?
                        WHERE pattern_name = ?
                    ''', (new_frequency, datetime.now().isoformat(), pattern_name))
                else:
                    # Insert new pattern
                    pattern_data = json.dumps({
                        'interaction_type': interaction_type,
                        'context_hash': hash(context),
                        'first_seen': datetime.now().isoformat()
                    })
                    
                    conn.execute('''
                        INSERT INTO usage_patterns 
                        (pattern_name, pattern_data, frequency, last_seen)
                        VALUES (?, ?, ?, ?)
                    ''', (pattern_name, pattern_data, 0.1, datetime.now().isoformat()))
        
        except Exception as e:
            logger.error(f"Failed to update usage pattern: {e}")
    
    def get_personalized_suggestions(self, context: str) -> List[str]:
        """Get personalized suggestions based on learned preferences"""
        suggestions = []
        
        try:
            # Get relevant preferences
            communication_style = self.user_preferences.get('communication_style', 'balanced')
            
            # Base suggestions
            if communication_style == 'formal':
                suggestions.extend([
                    "I would be happy to assist you with this request.",
                    "Please let me know if you need any additional information.",
                    "I appreciate your patience while I process this."
                ])
            elif communication_style == 'casual':
                suggestions.extend([
                    "Sure thing! Let me help you with that.",
                    "No problem! Here's what I found:",
                    "Got it! Let me take a look at this for you."
                ])
            else:
                suggestions.extend([
                    "I'll help you with that.",
                    "Here's what I can do for you:",
                    "Let me assist you with this."
                ])
            
            # Context-specific suggestions
            context_lower = context.lower()
            if 'urgent' in context_lower or 'asap' in context_lower:
                suggestions.insert(0, "I understand this is urgent. Let me prioritize this for you.")
            
            if 'help' in context_lower:
                suggestions.insert(0, f"I'm here to help! Based on your preferences, here are some options:")
        
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def load_preferences(self):
        """Load preferences from database"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute('SELECT preference_key, preference_value FROM learned_preferences')
                for pref_key, pref_value in cursor.fetchall():
                    try:
                        # Try to convert to appropriate type
                        if pref_value.replace('.', '').replace('-', '').isdigit():
                            self.user_preferences[pref_key] = float(pref_value)
                        else:
                            self.user_preferences[pref_key] = pref_value
                    except:
                        self.user_preferences[pref_key] = pref_value
        
        except Exception as e:
            logger.error(f"Failed to load preferences: {e}")
    
    def get_personalization_summary(self) -> Dict[str, Any]:
        """Get summary of personalization data"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Count interactions
                cursor = conn.execute('SELECT COUNT(*) FROM user_interactions')
                interaction_count = cursor.fetchone()[0]
                
                # Count preferences
                cursor = conn.execute('SELECT COUNT(*) FROM learned_preferences')
                preference_count = cursor.fetchone()[0]
                
                # Get top preferences
                cursor = conn.execute('''
                    SELECT preference_key, preference_value, confidence_score 
                    FROM learned_preferences 
                    ORDER BY confidence_score DESC 
                    LIMIT 5
                ''')
                top_preferences = [
                    {'key': row[0], 'value': row[1], 'confidence': row[2]}
                    for row in cursor.fetchall()
                ]
                
                return {
                    'total_interactions': interaction_count,
                    'learned_preferences': preference_count,
                    'top_preferences': top_preferences,
                    'personalization_level': min(1.0, interaction_count / 100.0)  # 0-1 scale
                }
        
        except Exception as e:
            logger.error(f"Failed to get personalization summary: {e}")
            return {}


class LocalAIManager(QObject):
    """Main local AI optimization and personalization manager"""
    
    def __init__(self):
        super().__init__()
        self.model_optimizer = AIModelOptimizer()
        self.model_hot_swapper = AIModelHotSwapper()
        self.personalization_engine = PersonalizationEngine()
        
        # Connect signals
        self._setup_connections()
        
    def _setup_connections(self):
        """Setup signal connections"""
        self.model_optimizer.optimization_completed.connect(self._on_optimization_completed)
        self.model_hot_swapper.model_swapped.connect(self._on_model_swapped)
        self.personalization_engine.preference_learned.connect(self._on_preference_learned)
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize local AI management"""
        # Get system specs
        system_specs = self._get_system_specs()
        
        # Initialize components
        results = {
            'system_specs': system_specs,
            'optimizer_ready': True,
            'hot_swapper_ready': True,
            'personalization_ready': True
        }
        
        logger.info("Local AI manager initialized")
        return results
    
    def _get_system_specs(self) -> Dict[str, Any]:
        """Get current system specifications"""
        try:
            memory = psutil.virtual_memory()
            
            specs = {
                'total_memory_gb': round(memory.total / (1024**3), 2),
                'available_memory_gb': round(memory.available / (1024**3), 2),
                'cpu_cores': psutil.cpu_count(),
                'cpu_usage': psutil.cpu_percent(),
                'gpu_available': self._check_gpu_availability(),
                'gpu_memory_gb': self._get_gpu_memory()
            }
            
            return specs
        
        except Exception as e:
            logger.error(f"Failed to get system specs: {e}")
            return {}
    
    def _check_gpu_availability(self) -> bool:
        """Check if GPU is available"""
        try:
            # Try to detect GPU
            if sys.platform == 'win32':
                import wmi
                c = wmi.WMI()
                for gpu in c.Win32_VideoController():
                    if gpu.Name and 'Microsoft' not in gpu.Name:
                        return True
        except:
            pass
        return False
    
    def _get_gpu_memory(self) -> float:
        """Get GPU memory in GB"""
        try:
            if sys.platform == 'win32':
                import wmi
                c = wmi.WMI()
                for gpu in c.Win32_VideoController():
                    if gpu.Name and 'Microsoft' not in gpu.Name and gpu.AdapterRAM:
                        return round(int(gpu.AdapterRAM) / (1024**3), 2)
        except:
            pass
        return 0.0
    
    def optimize_model(self, model_path: str) -> Dict[str, Any]:
        """Optimize a model for current system"""
        system_specs = self._get_system_specs()
        return self.model_optimizer.optimize_model_for_system(model_path, system_specs)
    
    def load_model(self, model_path: str) -> Optional[Any]:
        """Load model with hot-swapping"""
        return self.model_hot_swapper.load_model(model_path)
    
    def record_user_interaction(self, interaction_type: str, context: str, 
                              response: str, feedback: float = 0.0):
        """Record user interaction for personalization"""
        self.personalization_engine.record_interaction(
            interaction_type, context, response, feedback
        )
    
    def get_personalized_suggestions(self, context: str) -> List[str]:
        """Get personalized suggestions"""
        return self.personalization_engine.get_personalized_suggestions(context)
    
    def get_ai_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive AI status summary"""
        return {
            'system_specs': self._get_system_specs(),
            'model_optimizer': {
                'cached_optimizations': len(self.model_optimizer.optimization_cache),
                'model_profiles': len(self.model_optimizer.model_profiles)
            },
            'hot_swapper': self.model_hot_swapper.get_memory_usage_summary(),
            'personalization': self.personalization_engine.get_personalization_summary()
        }
    
    def _on_optimization_completed(self, optimization_type: str, data: Dict[str, Any]):
        """Handle optimization completion"""
        logger.info(f"AI optimization completed: {optimization_type}")
    
    def _on_model_swapped(self, old_model: str, new_model: str):
        """Handle model swap"""
        logger.info(f"Model swapped: {old_model} -> {new_model}")
    
    def _on_preference_learned(self, preference_key: str, data: Dict[str, Any]):
        """Handle preference learning"""
        logger.info(f"Preference learned: {preference_key} = {data['value']}")


# Global instance
_local_ai_manager = None
_manager_lock = threading.Lock()


def get_local_ai_manager() -> LocalAIManager:
    """Get the global local AI manager instance"""
    global _local_ai_manager
    
    if _local_ai_manager is None:
        with _manager_lock:
            if _local_ai_manager is None:
                _local_ai_manager = LocalAIManager()
    
    return _local_ai_manager


if __name__ == "__main__":
    # Test the local AI optimization
    print("Local AI Optimization Test")
    print("=" * 30)
    
    manager = get_local_ai_manager()
    init_results = manager.initialize()
    
    print("Initialization Results:")
    for key, value in init_results.items():
        print(f"  {key}: {value}")
    
    # Test model optimization
    test_model_path = "/path/to/test/model.gguf"
    optimization_config = manager.optimize_model(test_model_path)
    print(f"\nModel optimization config: {optimization_config}")
    
    # Test personalization
    manager.record_user_interaction(
        "chat", 
        "Help me with coding", 
        "Thanks! That's exactly what I needed.",
        1.0
    )
    
    suggestions = manager.get_personalized_suggestions("I need help with something")
    print(f"\nPersonalized suggestions: {suggestions}")
    
    # Get status summary
    status = manager.get_ai_status_summary()
    print(f"\nAI Status Summary:")
    for key, value in status.items():
        print(f"  {key}: {value}")