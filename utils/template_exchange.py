"""
Template Exchange System for Westfall Personal Assistant
Provides template management, sharing, and collaboration features
"""

import os
import json
import hashlib
import zipfile
import tempfile
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import shutil


@dataclass
class TemplateInfo:
    """Information about a template"""
    id: str
    name: str
    category: str
    description: str
    author: str
    version: str
    created_date: datetime
    modified_date: datetime
    file_size: int
    preview_url: Optional[str]
    download_count: int
    rating: float
    tags: List[str]
    variables: List[Dict[str, Any]]
    is_public: bool
    is_forked: bool
    parent_template: Optional[str]
    checksum: str


class TemplateExchangeManager:
    """Manages template sharing, versioning, and collaboration"""
    
    def __init__(self, templates_dir: str = None):
        self.templates_dir = templates_dir or os.path.join(os.getcwd(), "templates")
        self.local_templates = {}
        self.remote_templates = {}
        self.template_cache = {}
        
        # Template categories
        self.categories = {
            "business": ["invoices", "proposals", "contracts", "reports"],
            "personal": ["letters", "resumes", "notes", "journals"],
            "legal": ["agreements", "forms", "notices"],
            "marketing": ["emails", "brochures", "presentations"],
            "technical": ["documentation", "specifications", "manuals"]
        }
        
        # Variable types for dynamic content
        self.variable_types = {
            "text": {"input_type": "text", "validation": None},
            "number": {"input_type": "number", "validation": "numeric"},
            "date": {"input_type": "date", "validation": "date"},
            "email": {"input_type": "email", "validation": "email"},
            "phone": {"input_type": "tel", "validation": "phone"},
            "currency": {"input_type": "number", "validation": "currency"},
            "dropdown": {"input_type": "select", "validation": None},
            "checkbox": {"input_type": "checkbox", "validation": None},
            "textarea": {"input_type": "textarea", "validation": None}
        }
        
        self._init_directories()
        self._load_local_templates()
        
    def _init_directories(self):
        """Initialize template directories"""
        directories = [
            self.templates_dir,
            os.path.join(self.templates_dir, "local"),
            os.path.join(self.templates_dir, "downloaded"),
            os.path.join(self.templates_dir, "cache"),
            os.path.join(self.templates_dir, "previews"),
            os.path.join(self.templates_dir, "exports")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def _load_local_templates(self):
        """Load locally stored templates"""
        local_dir = os.path.join(self.templates_dir, "local")
        
        for template_file in os.listdir(local_dir):
            if template_file.endswith('.json'):
                template_path = os.path.join(local_dir, template_file)
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        
                    template_info = TemplateInfo(
                        id=template_data.get("id", template_file[:-5]),
                        name=template_data.get("name", "Untitled Template"),
                        category=template_data.get("category", "other"),
                        description=template_data.get("description", ""),
                        author=template_data.get("author", "Local User"),
                        version=template_data.get("version", "1.0.0"),
                        created_date=datetime.fromisoformat(
                            template_data.get("created_date", datetime.now().isoformat())
                        ),
                        modified_date=datetime.fromisoformat(
                            template_data.get("modified_date", datetime.now().isoformat())
                        ),
                        file_size=os.path.getsize(template_path),
                        preview_url=template_data.get("preview_url"),
                        download_count=template_data.get("download_count", 0),
                        rating=template_data.get("rating", 0.0),
                        tags=template_data.get("tags", []),
                        variables=template_data.get("variables", []),
                        is_public=template_data.get("is_public", False),
                        is_forked=template_data.get("is_forked", False),
                        parent_template=template_data.get("parent_template"),
                        checksum=self._calculate_checksum(template_path)
                    )
                    
                    self.local_templates[template_info.id] = template_info
                    
                except Exception as e:
                    print(f"Error loading template {template_file}: {e}")
                    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
        
    def create_template(self, name: str, category: str, content: str, 
                       variables: List[Dict[str, Any]] = None,
                       description: str = "", tags: List[str] = None,
                       is_public: bool = False) -> str:
        """Create a new template"""
        
        template_id = self._generate_template_id(name)
        current_time = datetime.now()
        
        template_data = {
            "id": template_id,
            "name": name,
            "category": category,
            "description": description,
            "author": "Local User",  # Would get from user settings
            "version": "1.0.0",
            "created_date": current_time.isoformat(),
            "modified_date": current_time.isoformat(),
            "content": content,
            "variables": variables or [],
            "tags": tags or [],
            "is_public": is_public,
            "is_forked": False,
            "parent_template": None,
            "rating": 0.0,
            "download_count": 0
        }
        
        # Save template to local directory
        template_path = os.path.join(self.templates_dir, "local", f"{template_id}.json")
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)
            
        # Create template info object
        template_info = TemplateInfo(
            id=template_id,
            name=name,
            category=category,
            description=description,
            author="Local User",
            version="1.0.0",
            created_date=current_time,
            modified_date=current_time,
            file_size=os.path.getsize(template_path),
            preview_url=None,
            download_count=0,
            rating=0.0,
            tags=tags or [],
            variables=variables or [],
            is_public=is_public,
            is_forked=False,
            parent_template=None,
            checksum=self._calculate_checksum(template_path)
        )
        
        self.local_templates[template_id] = template_info
        
        # Generate preview
        self._generate_preview(template_id, content)
        
        return template_id
        
    def _generate_template_id(self, name: str) -> str:
        """Generate a unique template ID"""
        base_id = name.lower().replace(" ", "-").replace("_", "-")
        counter = 1
        template_id = base_id
        
        while template_id in self.local_templates:
            template_id = f"{base_id}-{counter}"
            counter += 1
            
        return template_id
        
    def _generate_preview(self, template_id: str, content: str):
        """Generate a preview for the template"""
        preview_path = os.path.join(self.templates_dir, "previews", f"{template_id}.html")
        
        # Simple HTML preview generation
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Template Preview: {template_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .preview {{ border: 1px solid #ccc; padding: 20px; background: #f9f9f9; }}
        .variable {{ background: #ffffcc; padding: 2px 4px; border: 1px dashed #ccc; }}
    </style>
</head>
<body>
    <div class="preview">
        {self._convert_template_to_html(content)}
    </div>
</body>
</html>
"""
        
        with open(preview_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
    def _convert_template_to_html(self, content: str) -> str:
        """Convert template content to HTML for preview"""
        # Replace template variables with highlighted placeholders
        import re
        
        # Find variables in format {{variable_name}}
        def replace_variable(match):
            var_name = match.group(1)
            return f'<span class="variable">{{{{{var_name}}}}}</span>'
            
        html_content = re.sub(r'\{\{([^}]+)\}\}', replace_variable, content)
        html_content = html_content.replace('\n', '<br>')
        
        return html_content
        
    def update_template(self, template_id: str, **updates) -> bool:
        """Update an existing template"""
        if template_id not in self.local_templates:
            return False
            
        template_path = os.path.join(self.templates_dir, "local", f"{template_id}.json")
        if not os.path.exists(template_path):
            return False
            
        try:
            # Load current template data
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                
            # Apply updates
            for key, value in updates.items():
                if key in template_data:
                    template_data[key] = value
                    
            # Update modified date
            template_data["modified_date"] = datetime.now().isoformat()
            
            # Increment version if content changed
            if "content" in updates:
                version_parts = template_data["version"].split(".")
                version_parts[-1] = str(int(version_parts[-1]) + 1)
                template_data["version"] = ".".join(version_parts)
                
            # Save updated template
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
                
            # Update template info
            template_info = self.local_templates[template_id]
            for key, value in updates.items():
                if hasattr(template_info, key):
                    setattr(template_info, key, value)
                    
            template_info.modified_date = datetime.now()
            template_info.checksum = self._calculate_checksum(template_path)
            
            # Regenerate preview if content changed
            if "content" in updates:
                self._generate_preview(template_id, updates["content"])
                
            return True
            
        except Exception as e:
            print(f"Error updating template {template_id}: {e}")
            return False
            
    def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        if template_id not in self.local_templates:
            return False
            
        try:
            # Remove template file
            template_path = os.path.join(self.templates_dir, "local", f"{template_id}.json")
            if os.path.exists(template_path):
                os.remove(template_path)
                
            # Remove preview file
            preview_path = os.path.join(self.templates_dir, "previews", f"{template_id}.html")
            if os.path.exists(preview_path):
                os.remove(preview_path)
                
            # Remove from local templates
            del self.local_templates[template_id]
            
            return True
            
        except Exception as e:
            print(f"Error deleting template {template_id}: {e}")
            return False
            
    def fork_template(self, template_id: str, new_name: str = None) -> Optional[str]:
        """Create a fork of an existing template"""
        template_info = self.get_template(template_id)
        if not template_info:
            return None
            
        # Load template content
        template_content = self.get_template_content(template_id)
        if not template_content:
            return None
            
        # Create forked template
        fork_name = new_name or f"{template_info.name} (Fork)"
        fork_id = self.create_template(
            name=fork_name,
            category=template_info.category,
            content=template_content,
            variables=template_info.variables.copy(),
            description=f"Fork of {template_info.name}",
            tags=template_info.tags.copy(),
            is_public=False
        )
        
        # Update fork metadata
        self.update_template(
            fork_id,
            is_forked=True,
            parent_template=template_id
        )
        
        return fork_id
        
    def get_template(self, template_id: str) -> Optional[TemplateInfo]:
        """Get template information"""
        return self.local_templates.get(template_id)
        
    def get_template_content(self, template_id: str) -> Optional[str]:
        """Get template content"""
        template_path = os.path.join(self.templates_dir, "local", f"{template_id}.json")
        if not os.path.exists(template_path):
            return None
            
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                return template_data.get("content", "")
        except Exception as e:
            print(f"Error reading template {template_id}: {e}")
            return None
            
    def render_template(self, template_id: str, variables: Dict[str, Any] = None) -> Optional[str]:
        """Render template with variable substitution"""
        content = self.get_template_content(template_id)
        if not content:
            return None
            
        if not variables:
            variables = {}
            
        # Simple variable substitution
        import re
        
        def replace_variable(match):
            var_name = match.group(1).strip()
            return str(variables.get(var_name, f"{{{{{var_name}}}}}"))
            
        rendered_content = re.sub(r'\{\{([^}]+)\}\}', replace_variable, content)
        return rendered_content
        
    def search_templates(self, query: str = "", category: str = "", 
                        tags: List[str] = None, author: str = "") -> List[TemplateInfo]:
        """Search templates by various criteria"""
        results = []
        
        for template_info in self.local_templates.values():
            # Check query match
            if query:
                query_lower = query.lower()
                if (query_lower not in template_info.name.lower() and 
                    query_lower not in template_info.description.lower()):
                    continue
                    
            # Check category match
            if category and template_info.category != category:
                continue
                
            # Check tags match
            if tags and not any(tag in template_info.tags for tag in tags):
                continue
                
            # Check author match
            if author and author.lower() not in template_info.author.lower():
                continue
                
            results.append(template_info)
            
        # Sort by relevance (name match first, then description match)
        if query:
            query_lower = query.lower()
            results.sort(key=lambda t: (
                query_lower not in t.name.lower(),
                query_lower not in t.description.lower(),
                t.name.lower()
            ))
        else:
            results.sort(key=lambda t: t.modified_date, reverse=True)
            
        return results
        
    def get_templates_by_category(self) -> Dict[str, List[TemplateInfo]]:
        """Get templates organized by category"""
        categorized = {}
        
        for template_info in self.local_templates.values():
            category = template_info.category
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(template_info)
            
        # Sort each category by name
        for category in categorized:
            categorized[category].sort(key=lambda t: t.name.lower())
            
        return categorized
        
    def export_template(self, template_id: str, export_path: str = None) -> Optional[str]:
        """Export template as a ZIP file"""
        template_info = self.get_template(template_id)
        if not template_info:
            return None
            
        if not export_path:
            export_path = os.path.join(
                self.templates_dir, "exports", 
                f"{template_id}.zip"
            )
            
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add template JSON
                template_path = os.path.join(self.templates_dir, "local", f"{template_id}.json")
                zip_file.write(template_path, "template.json")
                
                # Add preview if exists
                preview_path = os.path.join(self.templates_dir, "previews", f"{template_id}.html")
                if os.path.exists(preview_path):
                    zip_file.write(preview_path, "preview.html")
                    
                # Add metadata
                metadata = {
                    "export_date": datetime.now().isoformat(),
                    "export_version": "1.0",
                    "template_info": asdict(template_info)
                }
                
                zip_file.writestr("metadata.json", json.dumps(metadata, indent=2, default=str))
                
            return export_path
            
        except Exception as e:
            print(f"Error exporting template {template_id}: {e}")
            return None
            
    def import_template(self, import_path: str) -> Optional[str]:
        """Import template from ZIP file"""
        try:
            with zipfile.ZipFile(import_path, 'r') as zip_file:
                # Extract template data
                with zip_file.open("template.json") as template_file:
                    template_data = json.load(template_file)
                    
                # Generate new ID to avoid conflicts
                original_id = template_data.get("id", "imported-template")
                new_id = self._generate_template_id(template_data.get("name", "Imported Template"))
                template_data["id"] = new_id
                
                # Update metadata
                template_data["created_date"] = datetime.now().isoformat()
                template_data["modified_date"] = datetime.now().isoformat()
                template_data["author"] = "Imported"
                
                # Save imported template
                template_path = os.path.join(self.templates_dir, "local", f"{new_id}.json")
                with open(template_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2, ensure_ascii=False)
                    
                # Extract preview if exists
                try:
                    with zip_file.open("preview.html") as preview_file:
                        preview_content = preview_file.read().decode('utf-8')
                        preview_path = os.path.join(self.templates_dir, "previews", f"{new_id}.html")
                        with open(preview_path, 'w', encoding='utf-8') as f:
                            f.write(preview_content)
                except KeyError:
                    # Preview doesn't exist, generate new one
                    self._generate_preview(new_id, template_data.get("content", ""))
                    
                # Create template info object
                template_info = TemplateInfo(
                    id=new_id,
                    name=template_data.get("name", "Imported Template"),
                    category=template_data.get("category", "other"),
                    description=template_data.get("description", ""),
                    author="Imported",
                    version=template_data.get("version", "1.0.0"),
                    created_date=datetime.now(),
                    modified_date=datetime.now(),
                    file_size=os.path.getsize(template_path),
                    preview_url=None,
                    download_count=0,
                    rating=0.0,
                    tags=template_data.get("tags", []),
                    variables=template_data.get("variables", []),
                    is_public=False,
                    is_forked=False,
                    parent_template=None,
                    checksum=self._calculate_checksum(template_path)
                )
                
                self.local_templates[new_id] = template_info
                
                return new_id
                
        except Exception as e:
            print(f"Error importing template: {e}")
            return None
            
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get template usage statistics"""
        total_templates = len(self.local_templates)
        categories = {}
        
        for template_info in self.local_templates.values():
            category = template_info.category
            categories[category] = categories.get(category, 0) + 1
            
        return {
            "total_templates": total_templates,
            "categories": categories,
            "total_variables": sum(
                len(t.variables) for t in self.local_templates.values()
            ),
            "public_templates": sum(
                1 for t in self.local_templates.values() if t.is_public
            ),
            "forked_templates": sum(
                1 for t in self.local_templates.values() if t.is_forked
            )
        }


# Global instance
template_manager = TemplateExchangeManager()


def get_template_manager() -> TemplateExchangeManager:
    """Get the global template exchange manager instance"""
    return template_manager