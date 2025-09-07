#!/usr/bin/env python3
"""
Advanced Calculator for Westfall Personal Assistant

Scientific calculator with history, memory functions, unit converter,
and programmer mode with hex/binary support.
"""

import asyncio
import logging
import json
import sqlite3
import math
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal, getcontext
import operator

logger = logging.getLogger(__name__)

# Set high precision for calculations
getcontext().prec = 50


class AdvancedCalculator:
    """Advanced calculator with scientific functions and history."""
    
    def __init__(self, config_dir: str = None, db_path: str = None):
        self.config_dir = config_dir or "~/.westfall_assistant"
        self.db_path = db_path or f"{self.config_dir}/calculator.db"
        
        # Calculator state
        self.memory = 0.0
        self.last_result = 0.0
        self.current_mode = "standard"  # "standard", "scientific", "programmer"
        self.angle_mode = "degrees"  # "degrees", "radians"
        
        # Programmer mode state
        self.number_base = 10  # 10 (decimal), 16 (hex), 8 (octal), 2 (binary)
        
        # Unit conversion categories
        self.unit_categories = {
            "length": {
                "mm": 0.001,
                "cm": 0.01,
                "m": 1.0,
                "km": 1000.0,
                "inch": 0.0254,
                "ft": 0.3048,
                "yard": 0.9144,
                "mile": 1609.344
            },
            "weight": {
                "g": 1.0,
                "kg": 1000.0,
                "oz": 28.3495,
                "lb": 453.592,
                "ton": 1000000.0
            },
            "temperature": {
                "celsius": lambda c: c,
                "fahrenheit": lambda f: (f - 32) * 5/9,
                "kelvin": lambda k: k - 273.15
            },
            "area": {
                "mm2": 0.000001,
                "cm2": 0.0001,
                "m2": 1.0,
                "km2": 1000000.0,
                "inch2": 0.00064516,
                "ft2": 0.092903,
                "acre": 4046.86
            },
            "volume": {
                "ml": 0.001,
                "l": 1.0,
                "m3": 1000.0,
                "gallon": 3.78541,
                "quart": 0.946353,
                "pint": 0.473176,
                "cup": 0.236588,
                "floz": 0.0295735
            }
        }
        
        # Mathematical constants
        self.constants = {
            "pi": math.pi,
            "e": math.e,
            "phi": (1 + math.sqrt(5)) / 2,  # Golden ratio
            "c": 299792458,  # Speed of light (m/s)
            "g": 9.80665,    # Standard gravity (m/s²)
            "h": 6.62607015e-34,  # Planck constant
            "avogadro": 6.02214076e23
        }
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for calculator history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create calculation history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS calculation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        expression TEXT NOT NULL,
                        result TEXT NOT NULL,
                        mode TEXT DEFAULT 'standard',
                        calculation_type TEXT DEFAULT 'basic',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT
                    )
                ''')
                
                # Create memory storage table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS memory_storage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        memory_slot TEXT NOT NULL,
                        value REAL NOT NULL,
                        description TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create unit conversion history
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversion_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        from_value REAL NOT NULL,
                        from_unit TEXT NOT NULL,
                        to_value REAL NOT NULL,
                        to_unit TEXT NOT NULL,
                        category TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create custom functions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS custom_functions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        expression TEXT NOT NULL,
                        parameters TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Calculator database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize calculator database: {e}")
            raise
    
    async def calculate(self, expression: str, mode: str = None) -> Dict:
        """Perform calculation and return result with metadata."""
        try:
            if mode:
                self.current_mode = mode
            
            # Clean and validate expression
            expression = self._clean_expression(expression)
            
            # Handle different modes
            if self.current_mode == "programmer":
                result = await self._calculate_programmer(expression)
            elif self.current_mode == "scientific":
                result = await self._calculate_scientific(expression)
            else:
                result = await self._calculate_standard(expression)
            
            # Store in history
            await self._store_calculation(expression, str(result["value"]), self.current_mode)
            
            # Update last result
            self.last_result = float(result["value"])
            
            return {
                "expression": expression,
                "result": result["value"],
                "formatted_result": result.get("formatted", str(result["value"])),
                "mode": self.current_mode,
                "calculation_type": result.get("type", "basic"),
                "metadata": result.get("metadata", {}),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Calculation failed: {e}")
            return {
                "expression": expression,
                "error": str(e),
                "success": False
            }
    
    def _clean_expression(self, expression: str) -> str:
        """Clean and normalize expression."""
        # Remove whitespace
        expression = expression.strip()
        
        # Replace constants
        for const_name, const_value in self.constants.items():
            expression = expression.replace(const_name, str(const_value))
        
        # Replace 'x' with '*' for multiplication
        expression = re.sub(r'(\d+)x(\d+)', r'\1*\2', expression)
        
        # Handle implicit multiplication (e.g., 2(3+4) -> 2*(3+4))
        expression = re.sub(r'(\d+)\(', r'\1*(', expression)
        expression = re.sub(r'\)(\d+)', r')*\1', expression)
        
        return expression
    
    async def _calculate_standard(self, expression: str) -> Dict:
        """Perform standard arithmetic calculation."""
        try:
            # Basic arithmetic evaluation
            result = eval(expression, {"__builtins__": {}}, {
                "abs": abs,
                "round": round,
                "max": max,
                "min": min,
                "sum": sum,
                "pow": pow
            })
            
            return {
                "value": result,
                "type": "arithmetic",
                "formatted": self._format_number(result)
            }
            
        except Exception as e:
            raise ValueError(f"Invalid arithmetic expression: {e}")
    
    async def _calculate_scientific(self, expression: str) -> Dict:
        """Perform scientific calculation with advanced functions."""
        try:
            # Create safe environment with scientific functions
            safe_dict = {
                "__builtins__": {},
                # Basic functions
                "abs": abs, "round": round, "max": max, "min": min, "sum": sum, "pow": pow,
                # Math functions
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "asin": math.asin, "acos": math.acos, "atan": math.atan,
                "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
                "log": math.log, "log10": math.log10, "log2": math.log2,
                "exp": math.exp, "sqrt": math.sqrt, "factorial": math.factorial,
                "degrees": math.degrees, "radians": math.radians,
                "floor": math.floor, "ceil": math.ceil,
                # Constants
                "pi": math.pi, "e": math.e,
                # Custom functions
                "last": self.last_result
            }
            
            # Handle angle mode for trigonometric functions
            if self.angle_mode == "degrees":
                expression = self._convert_trig_to_degrees(expression)
            
            result = eval(expression, safe_dict)
            
            return {
                "value": result,
                "type": "scientific",
                "formatted": self._format_number(result),
                "metadata": {"angle_mode": self.angle_mode}
            }
            
        except Exception as e:
            raise ValueError(f"Invalid scientific expression: {e}")
    
    async def _calculate_programmer(self, expression: str) -> Dict:
        """Perform programmer mode calculation with different number bases."""
        try:
            # Handle different number bases in input
            expression = self._convert_bases_in_expression(expression)
            
            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, {
                "abs": abs, "pow": pow,
                # Bitwise operations
                "and": operator.and_,
                "or": operator.or_,
                "xor": operator.xor,
                "not": operator.not_,
                "lshift": operator.lshift,
                "rshift": operator.rshift
            })
            
            # Convert result to different bases
            formatted_result = self._format_programmer_result(int(result))
            
            return {
                "value": result,
                "type": "programmer",
                "formatted": formatted_result,
                "metadata": {"base": self.number_base}
            }
            
        except Exception as e:
            raise ValueError(f"Invalid programmer expression: {e}")
    
    def _convert_trig_to_degrees(self, expression: str) -> str:
        """Convert trigonometric functions to work with degrees."""
        # Replace trig functions to handle degrees
        expression = re.sub(r'sin\((.*?)\)', r'sin(radians(\1))', expression)
        expression = re.sub(r'cos\((.*?)\)', r'cos(radians(\1))', expression)
        expression = re.sub(r'tan\((.*?)\)', r'tan(radians(\1))', expression)
        return expression
    
    def _convert_bases_in_expression(self, expression: str) -> str:
        """Convert different number bases to decimal for evaluation."""
        # Hex numbers (0x prefix)
        expression = re.sub(r'0x([0-9A-Fa-f]+)', lambda m: str(int(m.group(1), 16)), expression)
        
        # Binary numbers (0b prefix)
        expression = re.sub(r'0b([01]+)', lambda m: str(int(m.group(1), 2)), expression)
        
        # Octal numbers (0o prefix)
        expression = re.sub(r'0o([0-7]+)', lambda m: str(int(m.group(1), 8)), expression)
        
        return expression
    
    def _format_programmer_result(self, result: int) -> str:
        """Format result for programmer mode showing different bases."""
        return {
            "decimal": str(result),
            "hexadecimal": hex(result),
            "binary": bin(result),
            "octal": oct(result)
        }
    
    def _format_number(self, num: float) -> str:
        """Format number for display."""
        if abs(num) >= 1e15 or (abs(num) < 1e-4 and num != 0):
            return f"{num:.6e}"
        else:
            return f"{num:,.10g}"
    
    # Memory functions
    async def memory_store(self, value: float = None) -> bool:
        """Store value in memory (MS)."""
        try:
            if value is None:
                value = self.last_result
            
            self.memory = value
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO memory_storage (memory_slot, value, description)
                    VALUES ('main', ?, 'Main memory')
                ''', (value,))
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store in memory: {e}")
            return False
    
    async def memory_recall(self) -> float:
        """Recall value from memory (MR)."""
        return self.memory
    
    async def memory_add(self, value: float = None) -> bool:
        """Add to memory (M+)."""
        try:
            if value is None:
                value = self.last_result
            
            self.memory += value
            
            # Update in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE memory_storage SET value = ?, updated_at = ?
                    WHERE memory_slot = 'main'
                ''', (self.memory, datetime.now().isoformat()))
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add to memory: {e}")
            return False
    
    async def memory_subtract(self, value: float = None) -> bool:
        """Subtract from memory (M-)."""
        try:
            if value is None:
                value = self.last_result
            
            self.memory -= value
            
            # Update in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE memory_storage SET value = ?, updated_at = ?
                    WHERE memory_slot = 'main'
                ''', (self.memory, datetime.now().isoformat()))
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to subtract from memory: {e}")
            return False
    
    async def memory_clear(self) -> bool:
        """Clear memory (MC)."""
        try:
            self.memory = 0.0
            
            # Clear in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE memory_storage SET value = 0, updated_at = ?
                    WHERE memory_slot = 'main'
                ''', (datetime.now().isoformat(),))
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            return False
    
    # Unit conversion
    async def convert_units(self, value: float, from_unit: str, to_unit: str, 
                           category: str = None) -> Dict:
        """Convert between units."""
        try:
            # Auto-detect category if not provided
            if not category:
                category = self._detect_unit_category(from_unit, to_unit)
            
            if category not in self.unit_categories:
                raise ValueError(f"Unknown unit category: {category}")
            
            units = self.unit_categories[category]
            
            if category == "temperature":
                # Special handling for temperature
                result = self._convert_temperature(value, from_unit, to_unit)
            else:
                # Standard unit conversion using base units
                if from_unit not in units or to_unit not in units:
                    raise ValueError(f"Unknown units for category {category}")
                
                # Convert to base unit, then to target unit
                base_value = value * units[from_unit]
                result = base_value / units[to_unit]
            
            # Store conversion in history
            await self._store_conversion(value, from_unit, result, to_unit, category)
            
            return {
                "original_value": value,
                "original_unit": from_unit,
                "converted_value": result,
                "converted_unit": to_unit,
                "category": category,
                "formatted": f"{value} {from_unit} = {self._format_number(result)} {to_unit}"
            }
            
        except Exception as e:
            logger.error(f"Unit conversion failed: {e}")
            raise ValueError(f"Unit conversion failed: {e}")
    
    def _detect_unit_category(self, from_unit: str, to_unit: str) -> str:
        """Auto-detect unit category based on unit names."""
        for category, units in self.unit_categories.items():
            if from_unit in units and to_unit in units:
                return category
        
        raise ValueError(f"Could not determine category for units: {from_unit}, {to_unit}")
    
    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature between different scales."""
        # Convert to Celsius first
        if from_unit == "fahrenheit":
            celsius = (value - 32) * 5/9
        elif from_unit == "kelvin":
            celsius = value - 273.15
        else:  # celsius
            celsius = value
        
        # Convert from Celsius to target unit
        if to_unit == "fahrenheit":
            return celsius * 9/5 + 32
        elif to_unit == "kelvin":
            return celsius + 273.15
        else:  # celsius
            return celsius
    
    async def _store_calculation(self, expression: str, result: str, mode: str):
        """Store calculation in history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO calculation_history (expression, result, mode)
                    VALUES (?, ?, ?)
                ''', (expression, result, mode))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store calculation: {e}")
    
    async def _store_conversion(self, from_value: float, from_unit: str, 
                               to_value: float, to_unit: str, category: str):
        """Store unit conversion in history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO conversion_history 
                    (from_value, from_unit, to_value, to_unit, category)
                    VALUES (?, ?, ?, ?, ?)
                ''', (from_value, from_unit, to_value, to_unit, category))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store conversion: {e}")
    
    async def get_calculation_history(self, limit: int = 100) -> List[Dict]:
        """Get calculation history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM calculation_history
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                results = cursor.fetchall()
                return self._format_history(results)
                
        except Exception as e:
            logger.error(f"Failed to get calculation history: {e}")
            return []
    
    def _format_history(self, raw_history: List) -> List[Dict]:
        """Format raw database history into dictionaries."""
        history = []
        
        for row in raw_history:
            entry = {
                "id": row[0],
                "expression": row[1],
                "result": row[2],
                "mode": row[3],
                "calculation_type": row[4],
                "timestamp": row[5],
                "session_id": row[6]
            }
            history.append(entry)
        
        return history
    
    async def clear_history(self, history_type: str = "all") -> int:
        """Clear calculation history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if history_type == "calculations":
                    cursor.execute('DELETE FROM calculation_history')
                elif history_type == "conversions":
                    cursor.execute('DELETE FROM conversion_history')
                else:  # all
                    cursor.execute('DELETE FROM calculation_history')
                    cursor.execute('DELETE FROM conversion_history')
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            return 0
    
    async def get_available_units(self) -> Dict:
        """Get all available units by category."""
        return {
            category: list(units.keys()) 
            for category, units in self.unit_categories.items()
            if category != "temperature"
        }
    
    async def get_calculator_stats(self) -> Dict:
        """Get calculator usage statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total calculations
                cursor.execute('SELECT COUNT(*) FROM calculation_history')
                total_calculations = cursor.fetchone()[0]
                
                # Total conversions
                cursor.execute('SELECT COUNT(*) FROM conversion_history')
                total_conversions = cursor.fetchone()[0]
                
                # Calculations by mode
                cursor.execute('''
                    SELECT mode, COUNT(*) FROM calculation_history
                    GROUP BY mode
                ''')
                mode_stats = dict(cursor.fetchall())
                
                # Most used conversion categories
                cursor.execute('''
                    SELECT category, COUNT(*) FROM conversion_history
                    GROUP BY category
                    ORDER BY COUNT(*) DESC
                    LIMIT 5
                ''')
                conversion_stats = dict(cursor.fetchall())
                
                return {
                    "total_calculations": total_calculations,
                    "total_conversions": total_conversions,
                    "calculations_by_mode": mode_stats,
                    "popular_conversions": conversion_stats,
                    "memory_value": self.memory,
                    "current_mode": self.current_mode,
                    "angle_mode": self.angle_mode
                }
                
        except Exception as e:
            logger.error(f"Failed to get calculator stats: {e}")
            return {}