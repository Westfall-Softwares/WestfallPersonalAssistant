"""
Westfall Personal Assistant Localization System
Provides comprehensive multi-language support with context-aware translations
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import threading
from dataclasses import dataclass
from enum import Enum

class LanguageDirection(Enum):
    LTR = "ltr"  # Left to Right
    RTL = "rtl"  # Right to Left

class LocaleCategory(Enum):
    UI = "ui"
    ERROR = "error"
    BUSINESS = "business"
    TECHNICAL = "technical"
    HELP = "help"

@dataclass
class LanguageInfo:
    code: str
    name: str
    native_name: str
    direction: LanguageDirection
    region: str
    fallback: Optional[str] = None
    completion: float = 0.0  # Translation completion percentage

@dataclass
class TranslationEntry:
    key: str
    value: str
    context: Optional[str] = None
    category: LocaleCategory = LocaleCategory.UI
    pluralization: Optional[Dict[str, str]] = None
    variables: Optional[List[str]] = None
    last_updated: Optional[datetime] = None

class LocalizationManager:
    """
    Central localization management system for Westfall Personal Assistant
    """
    
    def __init__(self, localization_dir: str = None):
        self.localization_dir = Path(localization_dir or "localization")
        self.languages_dir = self.localization_dir / "languages"
        self.templates_dir = self.localization_dir / "templates"
        
        # Thread-safe translation cache
        self._translation_cache = {}
        self._cache_lock = threading.RLock()
        
        # Current locale settings
        self._current_language = "en"
        self._fallback_language = "en"
        
        # Supported languages with metadata
        self.supported_languages = {
            "en": LanguageInfo("en", "English", "English", LanguageDirection.LTR, "US"),
            "es": LanguageInfo("es", "Spanish", "Español", LanguageDirection.LTR, "ES", "en"),
            "fr": LanguageInfo("fr", "French", "Français", LanguageDirection.LTR, "FR", "en"),
            "de": LanguageInfo("de", "German", "Deutsch", LanguageDirection.LTR, "DE", "en"),
            "ar": LanguageInfo("ar", "Arabic", "العربية", LanguageDirection.RTL, "SA", "en"),
            "zh": LanguageInfo("zh", "Chinese", "中文", LanguageDirection.LTR, "CN", "en"),
            "ja": LanguageInfo("ja", "Japanese", "日本語", LanguageDirection.LTR, "JP", "en"),
            "pt": LanguageInfo("pt", "Portuguese", "Português", LanguageDirection.LTR, "BR", "en"),
            "ru": LanguageInfo("ru", "Russian", "Русский", LanguageDirection.LTR, "RU", "en"),
            "ko": LanguageInfo("ko", "Korean", "한국어", LanguageDirection.LTR, "KR", "en")
        }
        
        # Initialize directories and load translations
        self._initialize_directories()
        self._load_all_translations()
    
    def _initialize_directories(self):
        """Create necessary directories for localization"""
        self.localization_dir.mkdir(exist_ok=True)
        self.languages_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Create tools directory for utilities
        (self.localization_dir / "tools").mkdir(exist_ok=True)
    
    def _load_all_translations(self):
        """Load all available translations into cache"""
        with self._cache_lock:
            self._translation_cache.clear()
            
            for lang_code in self.supported_languages.keys():
                self._load_language_translations(lang_code)
    
    def _load_language_translations(self, language_code: str):
        """Load translations for a specific language"""
        lang_dir = self.languages_dir / language_code
        
        if not lang_dir.exists():
            return
        
        language_cache = {}
        
        # Load all JSON files in the language directory
        for json_file in lang_dir.glob("*.json"):
            category = json_file.stem
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                    language_cache[category] = translations
            except Exception as e:
                print(f"Error loading translations from {json_file}: {e}")
        
        self._translation_cache[language_code] = language_cache
    
    def set_language(self, language_code: str) -> bool:
        """Set the current language for the application"""
        if language_code not in self.supported_languages:
            print(f"Unsupported language: {language_code}")
            return False
        
        self._current_language = language_code
        
        # Set fallback language if specified
        lang_info = self.supported_languages[language_code]
        if lang_info.fallback:
            self._fallback_language = lang_info.fallback
        
        print(f"Language set to: {lang_info.native_name} ({language_code})")
        return True
    
    def get_current_language(self) -> str:
        """Get the current language code"""
        return self._current_language
    
    def get_language_info(self, language_code: str = None) -> LanguageInfo:
        """Get information about a language"""
        lang_code = language_code or self._current_language
        return self.supported_languages.get(lang_code)
    
    def translate(self, key: str, language: str = None, category: str = "ui", 
                  variables: Dict[str, Any] = None, plural_count: int = None) -> str:
        """
        Translate a key to the specified language with variable substitution and pluralization
        """
        target_language = language or self._current_language
        
        # Get translation from cache
        translation = self._get_translation_from_cache(key, target_language, category)
        
        # Fallback to default language if translation not found
        if translation is None and target_language != self._fallback_language:
            translation = self._get_translation_from_cache(key, self._fallback_language, category)
        
        # Ultimate fallback to the key itself
        if translation is None:
            translation = key
        
        # Handle pluralization
        if plural_count is not None and isinstance(translation, dict):
            translation = self._get_plural_form(translation, plural_count, target_language)
        
        # Variable substitution
        if variables:
            translation = self._substitute_variables(translation, variables)
        
        return translation
    
    def _get_translation_from_cache(self, key: str, language: str, category: str) -> Optional[str]:
        """Get translation from cache"""
        with self._cache_lock:
            lang_cache = self._translation_cache.get(language, {})
            category_cache = lang_cache.get(category, {})
            
            # Support nested keys (e.g., "dialog.confirm.title")
            keys = key.split('.')
            current = category_cache
            
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return None
            
            return current if isinstance(current, (str, dict)) else None
    
    def _get_plural_form(self, translations: Dict[str, str], count: int, language: str) -> str:
        """Get the appropriate plural form for the given count and language"""
        # English pluralization rules (can be extended for other languages)
        if language == "en":
            if count == 1:
                return translations.get("singular", translations.get("one", str(count)))
            else:
                return translations.get("plural", translations.get("other", str(count)))
        
        # Add more language-specific pluralization rules here
        elif language in ["es", "fr", "de", "pt"]:
            # Romance and Germanic languages (similar to English)
            if count == 1:
                return translations.get("singular", translations.get("one", str(count)))
            else:
                return translations.get("plural", translations.get("other", str(count)))
        
        elif language == "ru":
            # Russian has complex pluralization rules
            if count % 10 == 1 and count % 100 != 11:
                return translations.get("one", str(count))
            elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
                return translations.get("few", str(count))
            else:
                return translations.get("many", str(count))
        
        # Default fallback
        return translations.get("other", str(count))
    
    def _substitute_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in translated text"""
        if not isinstance(text, str):
            return str(text)
        
        # Support both {variable} and {{variable}} syntax
        for var_name, var_value in variables.items():
            text = text.replace(f"{{{var_name}}}", str(var_value))
            text = text.replace(f"{{{{{var_name}}}}}", str(var_value))
        
        return text
    
    def format_number(self, number: float, language: str = None) -> str:
        """Format number according to locale conventions"""
        target_language = language or self._current_language
        lang_info = self.get_language_info(target_language)
        
        # Basic locale-aware number formatting
        if lang_info and lang_info.region:
            try:
                import locale
                if target_language == "en":
                    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
                elif target_language == "es":
                    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
                elif target_language == "fr":
                    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
                elif target_language == "de":
                    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
                
                return locale.format_string("%.2f", number, grouping=True)
            except:
                pass
        
        # Fallback formatting
        return f"{number:,.2f}"
    
    def format_currency(self, amount: float, currency: str = "USD", language: str = None) -> str:
        """Format currency according to locale conventions"""
        target_language = language or self._current_language
        
        # Currency symbols by language/region
        currency_symbols = {
            "USD": {"en": "$", "es": "$", "fr": "$", "de": "$"},
            "EUR": {"en": "€", "es": "€", "fr": "€", "de": "€"},
            "GBP": {"en": "£", "es": "£", "fr": "£", "de": "£"},
            "JPY": {"en": "¥", "ja": "¥"},
            "CNY": {"en": "¥", "zh": "¥"}
        }
        
        symbol = currency_symbols.get(currency, {}).get(target_language, currency)
        formatted_number = self.format_number(amount, language)
        
        # Position symbol according to locale
        if target_language in ["fr"]:
            return f"{formatted_number} {symbol}"
        else:
            return f"{symbol}{formatted_number}"
    
    def format_date(self, date: datetime, format_type: str = "medium", language: str = None) -> str:
        """Format date according to locale conventions"""
        target_language = language or self._current_language
        
        # Date format patterns by language
        date_formats = {
            "en": {
                "short": "%m/%d/%Y",
                "medium": "%b %d, %Y",
                "long": "%B %d, %Y",
                "full": "%A, %B %d, %Y"
            },
            "es": {
                "short": "%d/%m/%Y",
                "medium": "%d %b %Y",
                "long": "%d de %B de %Y",
                "full": "%A, %d de %B de %Y"
            },
            "fr": {
                "short": "%d/%m/%Y",
                "medium": "%d %b %Y",
                "long": "%d %B %Y",
                "full": "%A %d %B %Y"
            },
            "de": {
                "short": "%d.%m.%Y",
                "medium": "%d. %b %Y",
                "long": "%d. %B %Y",
                "full": "%A, %d. %B %Y"
            }
        }
        
        format_pattern = date_formats.get(target_language, date_formats["en"])
        return date.strftime(format_pattern.get(format_type, format_pattern["medium"]))
    
    def get_available_languages(self) -> List[LanguageInfo]:
        """Get list of all available languages with their completion status"""
        languages = []
        
        for lang_code, lang_info in self.supported_languages.items():
            # Calculate translation completion
            completion = self._calculate_translation_completion(lang_code)
            lang_info.completion = completion
            languages.append(lang_info)
        
        return sorted(languages, key=lambda x: x.completion, reverse=True)
    
    def _calculate_translation_completion(self, language_code: str) -> float:
        """Calculate translation completion percentage for a language"""
        if language_code == "en":
            return 100.0  # English is the base language
        
        with self._cache_lock:
            en_cache = self._translation_cache.get("en", {})
            lang_cache = self._translation_cache.get(language_code, {})
            
            if not en_cache:
                return 0.0
            
            total_keys = 0
            translated_keys = 0
            
            for category, translations in en_cache.items():
                category_keys = self._count_translation_keys(translations)
                total_keys += category_keys
                
                lang_translations = lang_cache.get(category, {})
                lang_keys = self._count_translation_keys(lang_translations)
                translated_keys += lang_keys
            
            return (translated_keys / total_keys * 100) if total_keys > 0 else 0.0
    
    def _count_translation_keys(self, translations: Dict) -> int:
        """Recursively count translation keys in nested dictionaries"""
        count = 0
        for key, value in translations.items():
            if isinstance(value, dict):
                count += self._count_translation_keys(value)
            else:
                count += 1
        return count
    
    def extract_strings_from_code(self, source_directories: List[str]) -> Dict[str, List[str]]:
        """Extract translatable strings from source code"""
        extractable_patterns = [
            r't\(["\']([^"\']+)["\']\)',  # t("string")
            r'translate\(["\']([^"\']+)["\']\)',  # translate("string")
            r'_\(["\']([^"\']+)["\']\)',  # _("string")
            r'tr\(["\']([^"\']+)["\']\)',  # tr("string")
        ]
        
        extracted_strings = {}
        
        for source_dir in source_directories:
            source_path = Path(source_dir)
            if not source_path.exists():
                continue
            
            # Process Python files
            for py_file in source_path.rglob("*.py"):
                strings = self._extract_from_file(py_file, extractable_patterns)
                if strings:
                    extracted_strings[str(py_file)] = strings
            
            # Process JavaScript files
            for js_file in source_path.rglob("*.js"):
                strings = self._extract_from_file(js_file, extractable_patterns)
                if strings:
                    extracted_strings[str(js_file)] = strings
        
        return extracted_strings
    
    def _extract_from_file(self, file_path: Path, patterns: List[str]) -> List[str]:
        """Extract strings from a single file using regex patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            extracted = []
            for pattern in patterns:
                matches = re.findall(pattern, content)
                extracted.extend(matches)
            
            return list(set(extracted))  # Remove duplicates
        except Exception as e:
            print(f"Error extracting strings from {file_path}: {e}")
            return []
    
    def create_language_template(self, source_language: str = "en") -> Dict[str, Any]:
        """Create a template for a new language based on source language"""
        with self._cache_lock:
            source_cache = self._translation_cache.get(source_language, {})
            
            template = {}
            for category, translations in source_cache.items():
                template[category] = self._create_template_structure(translations)
            
            return template
    
    def _create_template_structure(self, translations: Dict) -> Dict:
        """Create template structure preserving keys but clearing values"""
        template = {}
        for key, value in translations.items():
            if isinstance(value, dict):
                template[key] = self._create_template_structure(value)
            else:
                template[key] = ""  # Empty string for translation
        return template
    
    def validate_translations(self, language_code: str) -> Dict[str, List[str]]:
        """Validate translations for completeness and consistency"""
        issues = {
            "missing_keys": [],
            "empty_translations": [],
            "variable_mismatches": [],
            "formatting_errors": []
        }
        
        with self._cache_lock:
            en_cache = self._translation_cache.get("en", {})
            lang_cache = self._translation_cache.get(language_code, {})
            
            for category, en_translations in en_cache.items():
                lang_translations = lang_cache.get(category, {})
                category_issues = self._validate_category_translations(
                    en_translations, lang_translations, category
                )
                
                for issue_type, issues_list in category_issues.items():
                    issues[issue_type].extend(issues_list)
        
        return issues
    
    def _validate_category_translations(self, en_translations: Dict, 
                                      lang_translations: Dict, category: str) -> Dict[str, List[str]]:
        """Validate translations within a category"""
        issues = {
            "missing_keys": [],
            "empty_translations": [],
            "variable_mismatches": [],
            "formatting_errors": []
        }
        
        for key, en_value in en_translations.items():
            full_key = f"{category}.{key}"
            
            if isinstance(en_value, dict):
                # Recursively validate nested structures
                lang_value = lang_translations.get(key, {})
                if isinstance(lang_value, dict):
                    nested_issues = self._validate_category_translations(
                        en_value, lang_value, full_key
                    )
                    for issue_type, issues_list in nested_issues.items():
                        issues[issue_type].extend(issues_list)
                else:
                    issues["missing_keys"].append(full_key)
            else:
                # Validate individual translation
                lang_value = lang_translations.get(key)
                
                if lang_value is None:
                    issues["missing_keys"].append(full_key)
                elif not lang_value.strip():
                    issues["empty_translations"].append(full_key)
                else:
                    # Check for variable consistency
                    en_vars = re.findall(r'\{([^}]+)\}', str(en_value))
                    lang_vars = re.findall(r'\{([^}]+)\}', str(lang_value))
                    
                    if set(en_vars) != set(lang_vars):
                        issues["variable_mismatches"].append(
                            f"{full_key}: EN vars {en_vars}, LANG vars {lang_vars}"
                        )
        
        return issues
    
    def export_translations(self, language_code: str, format_type: str = "json") -> str:
        """Export translations to various formats"""
        with self._cache_lock:
            lang_cache = self._translation_cache.get(language_code, {})
            
            if format_type == "json":
                return json.dumps(lang_cache, ensure_ascii=False, indent=2)
            elif format_type == "csv":
                return self._export_to_csv(lang_cache)
            elif format_type == "po":
                return self._export_to_po(lang_cache, language_code)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
    
    def _export_to_csv(self, translations: Dict) -> str:
        """Export translations to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Key", "Translation", "Category"])
        
        for category, trans_dict in translations.items():
            for key, value in self._flatten_translations(trans_dict).items():
                writer.writerow([key, value, category])
        
        return output.getvalue()
    
    def _export_to_po(self, translations: Dict, language_code: str) -> str:
        """Export translations to Gettext PO format"""
        po_content = f'''# Translation file for {language_code}
# Generated on {datetime.now().isoformat()}
msgid ""
msgstr ""
"Language: {language_code}\\n"
"Content-Type: text/plain; charset=UTF-8\\n"

'''
        
        for category, trans_dict in translations.items():
            for key, value in self._flatten_translations(trans_dict).items():
                po_content += f'''msgid "{key}"
msgstr "{value}"

'''
        
        return po_content
    
    def _flatten_translations(self, translations: Dict, prefix: str = "") -> Dict[str, str]:
        """Flatten nested translation dictionaries"""
        flattened = {}
        
        for key, value in translations.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(self._flatten_translations(value, full_key))
            else:
                flattened[full_key] = str(value)
        
        return flattened


# Global localization manager instance
_localization_manager = None

def get_localization_manager() -> LocalizationManager:
    """Get the global localization manager instance"""
    global _localization_manager
    if _localization_manager is None:
        _localization_manager = LocalizationManager()
    return _localization_manager

# Convenience functions
def t(key: str, **kwargs) -> str:
    """Translate a key (shorthand function)"""
    return get_localization_manager().translate(key, **kwargs)

def translate(key: str, language: str = None, category: str = "ui", 
              variables: Dict[str, Any] = None, plural_count: int = None) -> str:
    """Translate a key with full options"""
    return get_localization_manager().translate(
        key, language, category, variables, plural_count
    )

def set_language(language_code: str) -> bool:
    """Set the current language"""
    return get_localization_manager().set_language(language_code)

def get_current_language() -> str:
    """Get the current language code"""
    return get_localization_manager().get_current_language()

def format_number(number: float, language: str = None) -> str:
    """Format number according to locale"""
    return get_localization_manager().format_number(number, language)

def format_currency(amount: float, currency: str = "USD", language: str = None) -> str:
    """Format currency according to locale"""
    return get_localization_manager().format_currency(amount, currency, language)

def format_date(date: datetime, format_type: str = "medium", language: str = None) -> str:
    """Format date according to locale"""
    return get_localization_manager().format_date(date, format_type, language)