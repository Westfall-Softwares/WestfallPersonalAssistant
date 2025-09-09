#!/usr/bin/env python3
"""
Westfall Personal Assistant Localization Tools
Command-line utilities for managing translations
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
import csv
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.localization import LocalizationManager, get_localization_manager


class LocalizationCLI:
    """Command-line interface for localization management"""
    
    def __init__(self):
        self.localization_manager = get_localization_manager()
    
    def extract_strings(self, source_dirs: List[str], output_file: str = None):
        """Extract translatable strings from source code"""
        print("Extracting translatable strings from source code...")
        
        extracted = self.localization_manager.extract_strings_from_code(source_dirs)
        
        if not extracted:
            print("No translatable strings found.")
            return
        
        # Collect all unique strings
        all_strings = set()
        for file_strings in extracted.values():
            all_strings.update(file_strings)
        
        # Create extraction report
        report = {
            "extraction_date": str(self.localization_manager.supported_languages["en"].last_updated or "unknown"),
            "source_directories": source_dirs,
            "files_processed": len(extracted),
            "unique_strings": len(all_strings),
            "strings": sorted(list(all_strings)),
            "file_details": extracted
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"Extraction report saved to: {output_file}")
        
        # Print summary
        print(f"\nExtraction Summary:")
        print(f"  Files processed: {len(extracted)}")
        print(f"  Unique strings found: {len(all_strings)}")
        print(f"  Source directories: {', '.join(source_dirs)}")
        
        return report
    
    def validate_language(self, language_code: str):
        """Validate translations for a specific language"""
        print(f"Validating translations for: {language_code}")
        
        if language_code not in self.localization_manager.supported_languages:
            print(f"Error: Unsupported language '{language_code}'")
            return False
        
        issues = self.localization_manager.validate_translations(language_code)
        
        # Print validation results
        total_issues = sum(len(issue_list) for issue_list in issues.values())
        
        if total_issues == 0:
            print(f"✅ No issues found in {language_code} translations!")
            return True
        
        print(f"⚠️  Found {total_issues} issues in {language_code} translations:")
        
        for issue_type, issue_list in issues.items():
            if issue_list:
                print(f"\n{issue_type.upper().replace('_', ' ')} ({len(issue_list)} issues):")
                for issue in issue_list[:10]:  # Show first 10 issues
                    print(f"  - {issue}")
                if len(issue_list) > 10:
                    print(f"  ... and {len(issue_list) - 10} more")
        
        return False
    
    def create_language_template(self, target_language: str, source_language: str = "en"):
        """Create a new language template"""
        print(f"Creating template for {target_language} based on {source_language}")
        
        if target_language not in self.localization_manager.supported_languages:
            print(f"Error: Unsupported target language '{target_language}'")
            return False
        
        template = self.localization_manager.create_language_template(source_language)
        
        # Create language directory
        lang_dir = self.localization_manager.languages_dir / target_language
        lang_dir.mkdir(exist_ok=True)
        
        # Save template files
        for category, translations in template.items():
            template_file = lang_dir / f"{category}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
            print(f"Created: {template_file}")
        
        print(f"Language template for '{target_language}' created successfully!")
        return True
    
    def export_language(self, language_code: str, format_type: str = "json", output_file: str = None):
        """Export translations for a language"""
        print(f"Exporting {language_code} translations in {format_type} format...")
        
        if language_code not in self.localization_manager.supported_languages:
            print(f"Error: Unsupported language '{language_code}'")
            return False
        
        try:
            exported_data = self.localization_manager.export_translations(language_code, format_type)
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(exported_data)
                print(f"Exported to: {output_file}")
            else:
                print(exported_data)
            
            return True
            
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def show_completion_status(self):
        """Show translation completion status for all languages"""
        print("Translation Completion Status:")
        print("=" * 50)
        
        languages = self.localization_manager.get_available_languages()
        
        for lang_info in languages:
            completion = lang_info.completion
            bar_length = 30
            filled_length = int(bar_length * completion / 100)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            
            print(f"{lang_info.native_name:15} ({lang_info.code:2}) │{bar}│ {completion:5.1f}%")
        
        print("=" * 50)
    
    def import_csv_translations(self, csv_file: str, target_language: str):
        """Import translations from CSV file"""
        print(f"Importing translations from {csv_file} for {target_language}")
        
        if not os.path.exists(csv_file):
            print(f"Error: File '{csv_file}' not found")
            return False
        
        if target_language not in self.localization_manager.supported_languages:
            print(f"Error: Unsupported language '{target_language}'")
            return False
        
        # Read CSV file
        translations_by_category = {}
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    key = row.get('Key', '').strip()
                    translation = row.get('Translation', '').strip()
                    category = row.get('Category', 'ui').strip()
                    
                    if not key or not translation:
                        continue
                    
                    if category not in translations_by_category:
                        translations_by_category[category] = {}
                    
                    # Handle nested keys (e.g., "app.name")
                    keys = key.split('.')
                    current = translations_by_category[category]
                    
                    for i, k in enumerate(keys[:-1]):
                        if k not in current:
                            current[k] = {}
                        current = current[k]
                    
                    current[keys[-1]] = translation
            
            # Save translations to files
            lang_dir = self.localization_manager.languages_dir / target_language
            lang_dir.mkdir(exist_ok=True)
            
            imported_count = 0
            for category, translations in translations_by_category.items():
                category_file = lang_dir / f"{category}.json"
                
                # Load existing translations if file exists
                existing_translations = {}
                if category_file.exists():
                    with open(category_file, 'r', encoding='utf-8') as f:
                        existing_translations = json.load(f)
                
                # Merge with new translations
                existing_translations.update(translations)
                
                # Save updated translations
                with open(category_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_translations, f, ensure_ascii=False, indent=2)
                
                imported_count += len(translations)
                print(f"Updated: {category_file}")
            
            print(f"Successfully imported {imported_count} translations for {target_language}")
            
            # Reload translations
            self.localization_manager._load_language_translations(target_language)
            
            return True
            
        except Exception as e:
            print(f"Import failed: {e}")
            return False
    
    def generate_translation_report(self, output_file: str = None):
        """Generate comprehensive translation report"""
        print("Generating translation report...")
        
        languages = self.localization_manager.get_available_languages()
        
        report = {
            "generation_date": str(self.localization_manager.supported_languages["en"].last_updated or "unknown"),
            "total_languages": len(languages),
            "languages": []
        }
        
        for lang_info in languages:
            lang_data = {
                "code": lang_info.code,
                "name": lang_info.name,
                "native_name": lang_info.native_name,
                "direction": lang_info.direction.value,
                "region": lang_info.region,
                "completion": lang_info.completion,
                "fallback": lang_info.fallback
            }
            
            # Add validation results
            if lang_info.code != "en":  # Skip validation for base language
                issues = self.localization_manager.validate_translations(lang_info.code)
                lang_data["validation"] = {
                    "total_issues": sum(len(issue_list) for issue_list in issues.values()),
                    "issues_by_type": {issue_type: len(issue_list) for issue_type, issue_list in issues.items()}
                }
            
            report["languages"].append(lang_data)
        
        # Save report
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"Report saved to: {output_file}")
        
        # Print summary
        print(f"\nTranslation Report Summary:")
        print(f"  Total languages: {len(languages)}")
        print(f"  Average completion: {sum(l.completion for l in languages) / len(languages):.1f}%")
        
        complete_languages = [l for l in languages if l.completion > 95]
        print(f"  Fully translated (>95%): {len(complete_languages)} languages")
        
        return report


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Westfall Personal Assistant Localization Tools")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extract strings command
    extract_parser = subparsers.add_parser('extract', help='Extract translatable strings from source code')
    extract_parser.add_argument('source_dirs', nargs='+', help='Source directories to scan')
    extract_parser.add_argument('-o', '--output', help='Output file for extraction report')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate translations for a language')
    validate_parser.add_argument('language', help='Language code to validate')
    
    # Create template command
    template_parser = subparsers.add_parser('template', help='Create new language template')
    template_parser.add_argument('target_language', help='Target language code')
    template_parser.add_argument('-s', '--source', default='en', help='Source language (default: en)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export language translations')
    export_parser.add_argument('language', help='Language code to export')
    export_parser.add_argument('-f', '--format', choices=['json', 'csv', 'po'], default='json', help='Export format')
    export_parser.add_argument('-o', '--output', help='Output file')
    
    # Status command
    subparsers.add_parser('status', help='Show translation completion status')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import translations from CSV file')
    import_parser.add_argument('csv_file', help='CSV file containing translations')
    import_parser.add_argument('language', help='Target language code')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate translation report')
    report_parser.add_argument('-o', '--output', help='Output file for report')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = LocalizationCLI()
    
    try:
        if args.command == 'extract':
            cli.extract_strings(args.source_dirs, args.output)
        
        elif args.command == 'validate':
            success = cli.validate_language(args.language)
            return 0 if success else 1
        
        elif args.command == 'template':
            success = cli.create_language_template(args.target_language, args.source)
            return 0 if success else 1
        
        elif args.command == 'export':
            success = cli.export_language(args.language, args.format, args.output)
            return 0 if success else 1
        
        elif args.command == 'status':
            cli.show_completion_status()
        
        elif args.command == 'import':
            success = cli.import_csv_translations(args.csv_file, args.language)
            return 0 if success else 1
        
        elif args.command == 'report':
            cli.generate_translation_report(args.output)
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())