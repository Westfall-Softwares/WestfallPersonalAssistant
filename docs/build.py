#!/usr/bin/env python3
"""
Documentation Build System for Westfall Personal Assistant
Validates, generates, and deploys documentation
"""

import os
import sys
import re
import json
import yaml
import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import argparse
import subprocess
import hashlib

class DocumentationBuilder:
    """Main documentation build system"""
    
    def __init__(self, docs_dir: str = None):
        self.docs_dir = Path(docs_dir or "docs")
        self.build_dir = self.docs_dir / "_build"
        self.templates_dir = self.docs_dir / "_templates"
        self.assets_dir = self.docs_dir / "_assets"
        
        # Documentation metadata
        self.pages = {}
        self.index = {}
        self.links = {}
        self.categories = set()
        self.tags = set()
        
        # Build configuration
        self.config = {
            "title": "Westfall Personal Assistant Documentation",
            "description": "Complete documentation for the Westfall Personal Assistant",
            "version": "1.0.0",
            "author": "Westfall Softwares",
            "theme": "default",
            "output_formats": ["html", "json"],
            "search_enabled": True,
            "validation_strict": True
        }
        
        # Validation results
        self.errors = []
        self.warnings = []
        
    def validate_documentation(self) -> bool:
        """Validate all documentation files"""
        print("🔍 Validating Documentation...")
        
        valid = True
        
        # Check directory structure
        if not self._validate_directory_structure():
            valid = False
            
        # Validate all markdown files
        for md_file in self.docs_dir.rglob("*.md"):
            if not self._validate_markdown_file(md_file):
                valid = False
                
        # Check for broken links
        if not self._validate_links():
            valid = False
            
        # Validate front matter consistency
        if not self._validate_front_matter():
            valid = False
            
        # Report results
        self._report_validation_results()
        
        return valid and len(self.errors) == 0
        
    def _validate_directory_structure(self) -> bool:
        """Validate required directory structure"""
        required_dirs = [
            "_templates",
            "_assets", 
            "user",
            "user/features",
            "developer",
            "developer/api",
            "developer/plugins",
            "installation",
            "configuration",
            "reference"
        ]
        
        valid = True
        for dir_name in required_dirs:
            dir_path = self.docs_dir / dir_name
            if not dir_path.exists():
                self.errors.append(f"Missing required directory: {dir_path}")
                valid = False
                
        return valid
        
    def _validate_markdown_file(self, file_path: Path) -> bool:
        """Validate individual markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse front matter
            front_matter, body = self._parse_front_matter(content)
            
            if not front_matter:
                self.errors.append(f"{file_path}: Missing front matter")
                return False
                
            # Validate front matter fields
            if not self._validate_front_matter_fields(file_path, front_matter):
                return False
                
            # Store page info
            self.pages[str(file_path)] = {
                "path": file_path,
                "front_matter": front_matter,
                "body": body,
                "word_count": len(body.split()),
                "last_modified": datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
            }
            
            # Extract links
            self._extract_links(file_path, body)
            
            # Update metadata
            if front_matter.get("category"):
                self.categories.add(front_matter["category"])
            if front_matter.get("tags"):
                self.tags.update(front_matter["tags"])
                
            return True
            
        except Exception as e:
            self.errors.append(f"{file_path}: Error reading file - {e}")
            return False
            
    def _parse_front_matter(self, content: str) -> Tuple[Optional[Dict], str]:
        """Parse YAML front matter from markdown content"""
        if not content.startswith("---"):
            return None, content
            
        try:
            # Split front matter and body
            parts = content.split("---", 2)
            if len(parts) < 3:
                return None, content
                
            front_matter = yaml.safe_load(parts[1])
            body = parts[2].strip()
            
            return front_matter, body
            
        except yaml.YAMLError as e:
            return None, content
            
    def _validate_front_matter_fields(self, file_path: Path, front_matter: Dict) -> bool:
        """Validate front matter has required fields"""
        required_fields = ["title", "description", "category", "priority", "tags", "last_updated"]
        valid = True
        
        for field in required_fields:
            if field not in front_matter:
                self.errors.append(f"{file_path}: Missing required front matter field: {field}")
                valid = False
                
        # Validate field types and values
        if "priority" in front_matter:
            try:
                priority = int(front_matter["priority"])
                if priority < 1 or priority > 99:
                    self.warnings.append(f"{file_path}: Priority should be 1-99, got {priority}")
            except ValueError:
                self.errors.append(f"{file_path}: Priority must be a number")
                valid = False
                
        if "tags" in front_matter and not isinstance(front_matter["tags"], list):
            self.errors.append(f"{file_path}: Tags must be a list")
            valid = False
            
        if "category" in front_matter:
            allowed_categories = ["user", "developer", "installation", "configuration", "reference", "meta"]
            if front_matter["category"] not in allowed_categories:
                self.warnings.append(f"{file_path}: Unusual category: {front_matter['category']}")
                
        return valid
        
    def _extract_links(self, file_path: Path, content: str):
        """Extract all links from markdown content"""
        # Markdown link pattern: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        if str(file_path) not in self.links:
            self.links[str(file_path)] = []
            
        for match in re.finditer(link_pattern, content):
            link_text = match.group(1)
            link_url = match.group(2)
            
            self.links[str(file_path)].append({
                "text": link_text,
                "url": link_url,
                "type": "internal" if not link_url.startswith(("http", "mailto")) else "external"
            })
            
    def _validate_links(self) -> bool:
        """Validate all internal links"""
        valid = True
        
        for file_path, links in self.links.items():
            for link in links:
                if link["type"] == "internal":
                    # Resolve relative path
                    source_dir = Path(file_path).parent
                    target_path = source_dir / link["url"]
                    
                    try:
                        target_path = target_path.resolve()
                        if not target_path.exists():
                            self.errors.append(f"{file_path}: Broken internal link: {link['url']}")
                            valid = False
                    except Exception:
                        self.errors.append(f"{file_path}: Invalid link path: {link['url']}")
                        valid = False
                        
        return valid
        
    def _validate_front_matter(self) -> bool:
        """Validate front matter consistency across all files"""
        valid = True
        
        # Check for duplicate titles
        titles = {}
        for page_path, page_info in self.pages.items():
            title = page_info["front_matter"].get("title")
            if title:
                if title in titles:
                    self.warnings.append(f"Duplicate title '{title}' in {page_path} and {titles[title]}")
                else:
                    titles[title] = page_path
                    
        # Check for orphaned categories
        for category in self.categories:
            category_pages = [p for p in self.pages.values() 
                            if p["front_matter"].get("category") == category]
            if len(category_pages) < 2:
                self.warnings.append(f"Category '{category}' has only one page")
                
        return valid
        
    def _report_validation_results(self):
        """Report validation results"""
        print(f"📊 Validation Results:")
        print(f"   Pages validated: {len(self.pages)}")
        print(f"   Categories found: {len(self.categories)}")
        print(f"   Unique tags: {len(self.tags)}")
        print(f"   Links checked: {sum(len(links) for links in self.links.values())}")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")
                
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
                
        if not self.errors and not self.warnings:
            print("✅ All validation checks passed!")
            
    def generate_search_index(self) -> Dict:
        """Generate search index for documentation"""
        print("🔍 Generating Search Index...")
        
        index = {
            "pages": [],
            "categories": list(self.categories),
            "tags": list(self.tags),
            "generated": datetime.datetime.now().isoformat()
        }
        
        for page_path, page_info in self.pages.items():
            front_matter = page_info["front_matter"]
            
            # Create searchable content
            searchable_text = f"{front_matter.get('title', '')} {front_matter.get('description', '')} {page_info['body']}"
            
            page_entry = {
                "path": str(page_info["path"].relative_to(self.docs_dir)),
                "title": front_matter.get("title", ""),
                "description": front_matter.get("description", ""),
                "category": front_matter.get("category", ""),
                "tags": front_matter.get("tags", []),
                "priority": front_matter.get("priority", 50),
                "word_count": page_info["word_count"],
                "last_updated": front_matter.get("last_updated", ""),
                "search_text": searchable_text.lower()
            }
            
            index["pages"].append(page_entry)
            
        # Sort pages by priority and title
        index["pages"].sort(key=lambda x: (x["priority"], x["title"]))
        
        return index
        
    def generate_navigation(self) -> Dict:
        """Generate navigation structure"""
        navigation = {
            "categories": {},
            "quick_links": [],
            "recent_updates": []
        }
        
        # Group pages by category
        for page_path, page_info in self.pages.items():
            category = page_info["front_matter"].get("category", "other")
            
            if category not in navigation["categories"]:
                navigation["categories"][category] = []
                
            navigation["categories"][category].append({
                "title": page_info["front_matter"].get("title", ""),
                "path": str(page_info["path"].relative_to(self.docs_dir)),
                "description": page_info["front_matter"].get("description", ""),
                "priority": page_info["front_matter"].get("priority", 50)
            })
            
        # Sort each category by priority
        for category in navigation["categories"]:
            navigation["categories"][category].sort(key=lambda x: x["priority"])
            
        # Generate quick links (high priority pages)
        all_pages = []
        for page_info in self.pages.values():
            if page_info["front_matter"].get("priority", 50) <= 5:
                all_pages.append({
                    "title": page_info["front_matter"].get("title", ""),
                    "path": str(page_info["path"].relative_to(self.docs_dir)),
                    "priority": page_info["front_matter"].get("priority", 50)
                })
                
        navigation["quick_links"] = sorted(all_pages, key=lambda x: x["priority"])[:10]
        
        # Recent updates (last 30 days)
        recent_threshold = datetime.datetime.now() - datetime.timedelta(days=30)
        recent_pages = []
        
        for page_info in self.pages.values():
            if page_info["last_modified"] > recent_threshold:
                recent_pages.append({
                    "title": page_info["front_matter"].get("title", ""),
                    "path": str(page_info["path"].relative_to(self.docs_dir)),
                    "last_modified": page_info["last_modified"].isoformat()
                })
                
        navigation["recent_updates"] = sorted(recent_pages, 
                                            key=lambda x: x["last_modified"], 
                                            reverse=True)[:10]
        
        return navigation
        
    def build_html(self) -> bool:
        """Build HTML documentation"""
        print("🏗️  Building HTML Documentation...")
        
        html_dir = self.build_dir / "html"
        html_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate index and navigation
        search_index = self.generate_search_index()
        navigation = self.generate_navigation()
        
        # Save data files
        with open(html_dir / "search_index.json", "w", encoding="utf-8") as f:
            json.dump(search_index, f, indent=2, ensure_ascii=False)
            
        with open(html_dir / "navigation.json", "w", encoding="utf-8") as f:
            json.dump(navigation, f, indent=2, ensure_ascii=False)
            
        # Convert markdown to HTML (basic implementation)
        for page_path, page_info in self.pages.items():
            rel_path = page_info["path"].relative_to(self.docs_dir)
            html_path = html_dir / rel_path.with_suffix(".html")
            html_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Simple markdown to HTML conversion
            html_content = self._markdown_to_html(page_info["body"], page_info["front_matter"])
            
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
        print(f"✅ HTML documentation built in {html_dir}")
        return True
        
    def _markdown_to_html(self, content: str, front_matter: Dict) -> str:
        """Convert markdown to HTML (basic implementation)"""
        # This is a simplified conversion - in production you'd use a proper markdown parser
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{front_matter.get('title', 'Documentation')}</title>
    <meta name="description" content="{front_matter.get('description', '')}">
</head>
<body>
    <header>
        <h1>{front_matter.get('title', 'Documentation')}</h1>
        <p>{front_matter.get('description', '')}</p>
    </header>
    <main>
        <div class="content">
{content}
        </div>
    </main>
</body>
</html>"""
        return html
        
    def build_json(self) -> bool:
        """Build JSON documentation export"""
        print("📄 Building JSON Documentation...")
        
        json_dir = self.build_dir / "json"
        json_dir.mkdir(parents=True, exist_ok=True)
        
        # Create comprehensive JSON export
        export_data = {
            "metadata": {
                "title": self.config["title"],
                "description": self.config["description"],
                "version": self.config["version"],
                "generated": datetime.datetime.now().isoformat(),
                "total_pages": len(self.pages),
                "categories": list(self.categories),
                "tags": list(self.tags)
            },
            "pages": {},
            "navigation": self.generate_navigation(),
            "search_index": self.generate_search_index()
        }
        
        # Add all pages
        for page_path, page_info in self.pages.items():
            rel_path = str(page_info["path"].relative_to(self.docs_dir))
            export_data["pages"][rel_path] = {
                "front_matter": page_info["front_matter"],
                "content": page_info["body"],
                "word_count": page_info["word_count"],
                "last_modified": page_info["last_modified"].isoformat()
            }
            
        # Save complete export
        with open(json_dir / "documentation.json", "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
            
        print(f"✅ JSON documentation built in {json_dir}")
        return True
        
    def deploy_to_app(self) -> bool:
        """Deploy documentation to in-app help system"""
        print("🚀 Deploying to In-App Help System...")
        
        app_help_dir = Path("../help_system/docs")  # Relative to app directory
        app_help_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy JSON export for app use
        json_file = self.build_dir / "json" / "documentation.json"
        if json_file.exists():
            import shutil
            shutil.copy2(json_file, app_help_dir / "documentation.json")
            
            # Create lightweight search index for app
            search_index = self.generate_search_index()
            with open(app_help_dir / "search_index.json", "w", encoding="utf-8") as f:
                json.dump(search_index, f, indent=2, ensure_ascii=False)
                
            print("✅ Documentation deployed to in-app help system")
            return True
        else:
            self.errors.append("JSON documentation not found - run build first")
            return False
            
    def lint_documentation(self) -> bool:
        """Run documentation linting checks"""
        print("📝 Linting Documentation...")
        
        lint_passed = True
        
        # Check writing style
        for page_path, page_info in self.pages.items():
            content = page_info["body"]
            
            # Check for common style issues
            if "click here" in content.lower():
                self.warnings.append(f"{page_path}: Avoid 'click here' - use descriptive link text")
                
            # Check for very long paragraphs
            paragraphs = content.split("\n\n")
            for i, para in enumerate(paragraphs):
                if len(para.split()) > 200:
                    self.warnings.append(f"{page_path}: Paragraph {i+1} is very long ({len(para.split())} words)")
                    
            # Check for missing alt text in images
            img_pattern = r'!\[([^\]]*)\]\([^)]+\)'
            for match in re.finditer(img_pattern, content):
                alt_text = match.group(1)
                if not alt_text.strip():
                    self.errors.append(f"{page_path}: Image missing alt text")
                    lint_passed = False
                    
        return lint_passed
        
    def generate_stats(self) -> Dict:
        """Generate documentation statistics"""
        stats = {
            "overview": {
                "total_pages": len(self.pages),
                "total_words": sum(p["word_count"] for p in self.pages.values()),
                "categories": len(self.categories),
                "tags": len(self.tags),
                "total_links": sum(len(links) for links in self.links.values())
            },
            "by_category": {},
            "recent_activity": {},
            "quality_metrics": {
                "pages_with_descriptions": 0,
                "pages_with_tags": 0,
                "average_word_count": 0,
                "broken_links": len(self.errors)  # Approximate
            }
        }
        
        # Stats by category
        for category in self.categories:
            category_pages = [p for p in self.pages.values() 
                            if p["front_matter"].get("category") == category]
            stats["by_category"][category] = {
                "pages": len(category_pages),
                "total_words": sum(p["word_count"] for p in category_pages)
            }
            
        # Quality metrics
        for page_info in self.pages.values():
            if page_info["front_matter"].get("description"):
                stats["quality_metrics"]["pages_with_descriptions"] += 1
            if page_info["front_matter"].get("tags"):
                stats["quality_metrics"]["pages_with_tags"] += 1
                
        if self.pages:
            stats["quality_metrics"]["average_word_count"] = (
                stats["overview"]["total_words"] / len(self.pages)
            )
            
        return stats

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Westfall Personal Assistant Documentation Builder")
    parser.add_argument("command", choices=[
        "validate", "build", "lint", "deploy", "stats", "all"
    ], help="Command to execute")
    parser.add_argument("--docs-dir", default="docs", help="Documentation directory")
    parser.add_argument("--format", choices=["html", "json", "all"], default="all", 
                       help="Output format for build command")
    parser.add_argument("--strict", action="store_true", help="Strict validation mode")
    
    args = parser.parse_args()
    
    # Initialize builder
    builder = DocumentationBuilder(args.docs_dir)
    builder.config["validation_strict"] = args.strict
    
    success = True
    
    if args.command in ["validate", "all"]:
        success &= builder.validate_documentation()
        
    if args.command in ["lint", "all"]:
        success &= builder.lint_documentation()
        
    if args.command in ["build", "all"]:
        if args.format in ["html", "all"]:
            success &= builder.build_html()
        if args.format in ["json", "all"]:
            success &= builder.build_json()
            
    if args.command in ["deploy", "all"]:
        success &= builder.deploy_to_app()
        
    if args.command in ["stats", "all"]:
        stats = builder.generate_stats()
        print("\n📊 Documentation Statistics:")
        print(json.dumps(stats, indent=2))
        
    # Final report
    if success:
        print("\n🎉 Documentation build completed successfully!")
        return 0
    else:
        print("\n❌ Documentation build failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())