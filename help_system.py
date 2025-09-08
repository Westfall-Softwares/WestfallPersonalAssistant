#!/usr/bin/env python3
"""
In-App Help System for Westfall Personal Assistant
Provides context-sensitive help and documentation browsing
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QLineEdit,
    QListWidget, QListWidgetItem, QSplitter, QPushButton, QLabel,
    QComboBox, QTabWidget, QTreeWidget, QTreeWidgetItem, QFrame,
    QScrollArea, QDialog, QDialogButtonBox, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt5.QtGui import QFont, QIcon, QPixmap, QTextDocument

class DocumentationLoader(QThread):
    """Background thread for loading documentation"""
    
    documentation_loaded = pyqtSignal(dict)
    progress_updated = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, docs_dir: str):
        super().__init__()
        self.docs_dir = Path(docs_dir)
        
    def run(self):
        """Load documentation in background"""
        try:
            # Check if documentation index exists
            index_file = self.docs_dir / "_build" / "json" / "documentation.json"
            
            if index_file.exists():
                self.progress_updated.emit(20)
                # Load pre-built documentation
                with open(index_file, 'r', encoding='utf-8') as f:
                    docs_data = json.load(f)
                self.progress_updated.emit(100)
                self.documentation_loaded.emit(docs_data)
            else:
                # Build documentation on-the-fly
                self.progress_updated.emit(10)
                docs_data = self._build_documentation()
                self.progress_updated.emit(100)
                self.documentation_loaded.emit(docs_data)
                
        except Exception as e:
            self.error_occurred.emit(f"Failed to load documentation: {e}")
            
    def _build_documentation(self) -> Dict:
        """Build documentation structure from markdown files"""
        docs_data = {
            "metadata": {
                "title": "Westfall Personal Assistant Documentation",
                "version": "1.0.0",
                "generated": "2025-09-08"
            },
            "pages": {},
            "navigation": {"categories": {}},
            "search_index": {"pages": []}
        }
        
        self.progress_updated.emit(30)
        
        # Find all markdown files
        md_files = list(self.docs_dir.rglob("*.md"))
        total_files = len(md_files)
        
        for i, md_file in enumerate(md_files):
            if md_file.name.startswith('_'):  # Skip template files
                continue
                
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse front matter and content
                front_matter, body = self._parse_front_matter(content)
                
                rel_path = str(md_file.relative_to(self.docs_dir))
                docs_data["pages"][rel_path] = {
                    "front_matter": front_matter or {},
                    "content": body,
                    "path": rel_path
                }
                
                # Update search index
                if front_matter:
                    docs_data["search_index"]["pages"].append({
                        "path": rel_path,
                        "title": front_matter.get("title", ""),
                        "description": front_matter.get("description", ""),
                        "category": front_matter.get("category", ""),
                        "tags": front_matter.get("tags", []),
                        "search_text": f"{front_matter.get('title', '')} {front_matter.get('description', '')} {body}".lower()
                    })
                    
                    # Update navigation
                    category = front_matter.get("category", "other")
                    if category not in docs_data["navigation"]["categories"]:
                        docs_data["navigation"]["categories"][category] = []
                        
                    docs_data["navigation"]["categories"][category].append({
                        "title": front_matter.get("title", ""),
                        "path": rel_path,
                        "priority": front_matter.get("priority", 50)
                    })
                    
            except Exception as e:
                print(f"Error processing {md_file}: {e}")
                
            # Update progress
            progress = 30 + int((i + 1) / total_files * 60)
            self.progress_updated.emit(progress)
            
        # Sort navigation by priority
        for category in docs_data["navigation"]["categories"]:
            docs_data["navigation"]["categories"][category].sort(
                key=lambda x: x["priority"]
            )
            
        return docs_data
        
    def _parse_front_matter(self, content: str):
        """Parse YAML front matter from markdown"""
        if not content.startswith("---"):
            return None, content
            
        try:
            parts = content.split("---", 2)
            if len(parts) < 3:
                return None, content
                
            # Simple YAML parsing for front matter
            front_matter = {}
            yaml_content = parts[1].strip()
            
            for line in yaml_content.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().strip('"')
                    value = value.strip().strip('"')
                    
                    # Handle lists
                    if value.startswith('[') and value.endswith(']'):
                        value = [v.strip().strip('"') for v in value[1:-1].split(',')]
                    # Handle numbers
                    elif value.isdigit():
                        value = int(value)
                        
                    front_matter[key] = value
                    
            body = parts[2].strip()
            return front_matter, body
            
        except Exception:
            return None, content

class HelpSearchWidget(QWidget):
    """Search interface for documentation"""
    
    search_requested = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search documentation...")
        self.search_input.returnPressed.connect(self.perform_search)
        layout.addWidget(self.search_input)
        
        # Search button
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.perform_search)
        layout.addWidget(search_btn)
        
        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.currentTextChanged.connect(self.perform_search)
        layout.addWidget(self.category_filter)
        
        self.setLayout(layout)
        
    def perform_search(self):
        """Emit search signal"""
        query = self.search_input.text()
        category = self.category_filter.currentText()
        
        if category == "All Categories":
            category = ""
            
        search_term = f"{query} category:{category}".strip()
        self.search_requested.emit(search_term)
        
    def update_categories(self, categories: List[str]):
        """Update category filter with available categories"""
        self.category_filter.clear()
        self.category_filter.addItem("All Categories")
        for category in sorted(categories):
            self.category_filter.addItem(category.title())

class NavigationTreeWidget(QTreeWidget):
    """Navigation tree for documentation structure"""
    
    page_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.itemClicked.connect(self.on_item_clicked)
        
    def populate_navigation(self, navigation_data: Dict):
        """Populate tree with navigation structure"""
        self.clear()
        
        categories = navigation_data.get("categories", {})
        
        for category, pages in categories.items():
            category_item = QTreeWidgetItem([category.title()])
            category_item.setData(0, Qt.UserRole, None)  # No page for category
            
            for page in pages:
                page_item = QTreeWidgetItem([page["title"]])
                page_item.setData(0, Qt.UserRole, page["path"])
                category_item.addChild(page_item)
                
            self.addTopLevelItem(category_item)
            
        # Expand all categories
        self.expandAll()
        
    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item selection"""
        page_path = item.data(0, Qt.UserRole)
        if page_path:
            self.page_selected.emit(page_path)

class DocumentationViewer(QTextBrowser):
    """Enhanced text browser for displaying documentation"""
    
    link_clicked = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setOpenExternalLinks(False)
        self.anchorClicked.connect(self.on_link_clicked)
        
        # Set up styling
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        
    def on_link_clicked(self, url: QUrl):
        """Handle link clicks"""
        url_str = url.toString()
        
        if url_str.startswith("http"):
            # External link - open in system browser
            import webbrowser
            webbrowser.open(url_str)
        else:
            # Internal link - emit signal
            self.link_clicked.emit(url_str)
            
    def display_markdown(self, content: str, base_path: str = ""):
        """Convert and display markdown content"""
        # Simple markdown to HTML conversion
        html = self._markdown_to_html(content, base_path)
        self.setHtml(html)
        
    def _markdown_to_html(self, content: str, base_path: str) -> str:
        """Convert markdown to HTML (simplified)"""
        html = content
        
        # Headers
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        
        # Bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Code blocks
        html = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        
        # Links
        html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
        
        # Lists
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        
        # Tables (basic)
        lines = html.split('\n')
        in_table = False
        table_html = []
        
        for line in lines:
            if '|' in line and not in_table:
                in_table = True
                table_html.append('<table border="1">')
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                table_html.append('<tr>' + ''.join(f'<th>{cell}</th>' for cell in cells) + '</tr>')
            elif '|' in line and in_table:
                if line.strip().startswith('|---'):
                    continue  # Skip separator row
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                table_html.append('<tr>' + ''.join(f'<td>{cell}</td>' for cell in cells) + '</tr>')
            elif in_table and '|' not in line:
                in_table = False
                table_html.append('</table>')
                table_html.append(line)
            else:
                table_html.append(line)
                
        if in_table:
            table_html.append('</table>')
            
        html = '\n'.join(table_html)
        
        # Paragraphs
        paragraphs = html.split('\n\n')
        html_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para and not para.startswith('<'):
                para = f'<p>{para}</p>'
            html_paragraphs.append(para)
            
        html = '\n\n'.join(html_paragraphs)
        
        # Add CSS styling
        css = """
        <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }
        h2 { color: #34495e; border-bottom: 1px solid #bdc3c7; }
        h3 { color: #7f8c8d; }
        code { background-color: #f8f9fa; padding: 2px 4px; border-radius: 3px; }
        pre { background-color: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        th, td { padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        a { color: #3498db; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .warning { background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; }
        .error { background-color: #f8d7da; padding: 10px; border-left: 4px solid #dc3545; }
        .info { background-color: #d1ecf1; padding: 10px; border-left: 4px solid #17a2b8; }
        </style>
        """
        
        return f"<html><head>{css}</head><body>{html}</body></html>"

class HelpSystemWidget(QWidget):
    """Main help system widget"""
    
    def __init__(self, docs_dir: str = "docs"):
        super().__init__()
        self.docs_dir = docs_dir
        self.documentation = {}
        self.search_index = []
        self.current_page = ""
        
        self.init_ui()
        self.load_documentation()
        
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📚 Help & Documentation")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Search widget
        self.search_widget = HelpSearchWidget()
        self.search_widget.search_requested.connect(self.perform_search)
        layout.addWidget(self.search_widget)
        
        # Main content area
        splitter = QSplitter(Qt.Horizontal)
        
        # Left sidebar - navigation
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        nav_label = QLabel("📑 Navigation")
        nav_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        left_layout.addWidget(nav_label)
        
        self.navigation_tree = NavigationTreeWidget()
        self.navigation_tree.page_selected.connect(self.show_page)
        left_layout.addWidget(self.navigation_tree)
        
        # Quick links
        quick_label = QLabel("🔗 Quick Links")
        quick_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        left_layout.addWidget(quick_label)
        
        self.quick_links = QListWidget()
        self.quick_links.itemClicked.connect(self.on_quick_link_clicked)
        left_layout.addWidget(self.quick_links)
        
        splitter.addWidget(left_widget)
        
        # Right side - content viewer
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Breadcrumb
        self.breadcrumb = QLabel("")
        self.breadcrumb.setStyleSheet("color: #666; font-size: 9px;")
        right_layout.addWidget(self.breadcrumb)
        
        # Content viewer
        self.content_viewer = DocumentationViewer()
        self.content_viewer.link_clicked.connect(self.on_internal_link)
        right_layout.addWidget(self.content_viewer)
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        
        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        nav_buttons.addWidget(self.back_btn)
        
        nav_buttons.addStretch()
        
        self.print_btn = QPushButton("🖨️ Print")
        self.print_btn.clicked.connect(self.print_page)
        nav_buttons.addWidget(self.print_btn)
        
        self.export_btn = QPushButton("💾 Export")
        self.export_btn.clicked.connect(self.export_page)
        nav_buttons.addWidget(self.export_btn)
        
        right_layout.addLayout(nav_buttons)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 550])
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel("Loading documentation...")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # History for back navigation
        self.page_history = []
        
    def load_documentation(self):
        """Load documentation in background"""
        self.status_label.setText("Loading documentation...")
        
        self.loader = DocumentationLoader(self.docs_dir)
        self.loader.documentation_loaded.connect(self.on_documentation_loaded)
        self.loader.error_occurred.connect(self.on_load_error)
        self.loader.start()
        
    def on_documentation_loaded(self, docs_data: Dict):
        """Handle loaded documentation"""
        self.documentation = docs_data
        
        # Populate navigation
        navigation = docs_data.get("navigation", {})
        self.navigation_tree.populate_navigation(navigation)
        
        # Update search categories
        categories = list(navigation.get("categories", {}).keys())
        self.search_widget.update_categories(categories)
        
        # Set search index
        self.search_index = docs_data.get("search_index", {}).get("pages", [])
        
        # Populate quick links
        self.populate_quick_links()
        
        # Show index page
        if "index.md" in docs_data.get("pages", {}):
            self.show_page("index.md")
        else:
            self.show_welcome_page()
            
        self.status_label.setText(f"Documentation loaded - {len(self.search_index)} pages available")
        
    def on_load_error(self, error_message: str):
        """Handle documentation load error"""
        self.status_label.setText(f"Error: {error_message}")
        QMessageBox.warning(self, "Documentation Load Error", error_message)
        
    def populate_quick_links(self):
        """Populate quick links list"""
        quick_links = [
            ("Getting Started", "user/getting-started.md"),
            ("Installation", "installation/windows.md"),
            ("Troubleshooting", "user/troubleshooting.md"),
            ("FAQ", "user/faq.md"),
            ("Keyboard Shortcuts", "reference/commands.md")
        ]
        
        for title, path in quick_links:
            if path in self.documentation.get("pages", {}):
                item = QListWidgetItem(title)
                item.setData(Qt.UserRole, path)
                self.quick_links.addItem(item)
                
    def on_quick_link_clicked(self, item: QListWidgetItem):
        """Handle quick link selection"""
        path = item.data(Qt.UserRole)
        if path:
            self.show_page(path)
            
    def show_page(self, page_path: str):
        """Display a documentation page"""
        if page_path not in self.documentation.get("pages", {}):
            self.content_viewer.setHtml(f"<h1>Page Not Found</h1><p>The page '{page_path}' could not be found.</p>")
            return
            
        # Add to history
        if self.current_page and self.current_page != page_path:
            self.page_history.append(self.current_page)
            self.back_btn.setEnabled(True)
            
        self.current_page = page_path
        
        page_data = self.documentation["pages"][page_path]
        content = page_data["content"]
        front_matter = page_data.get("front_matter", {})
        
        # Update breadcrumb
        category = front_matter.get("category", "")
        title = front_matter.get("title", page_path)
        self.breadcrumb.setText(f"📁 {category.title()} > {title}")
        
        # Display content
        self.content_viewer.display_markdown(content, page_path)
        
        self.status_label.setText(f"Viewing: {title}")
        
    def show_welcome_page(self):
        """Show welcome page when no index is available"""
        welcome_content = """
        # Welcome to Westfall Personal Assistant Help
        
        This is the integrated help system for Westfall Personal Assistant.
        
        ## Getting Started
        
        - Use the navigation tree on the left to browse documentation
        - Use the search box to find specific information
        - Click on quick links for common topics
        
        ## Need Help?
        
        If you can't find what you're looking for:
        
        1. Try the AI Assistant (Ctrl+Space)
        2. Check our online documentation
        3. Visit our community forums
        
        *Documentation is loading in the background...*
        """
        
        self.content_viewer.display_markdown(welcome_content)
        
    def perform_search(self, query: str):
        """Perform documentation search"""
        if not query.strip():
            return
            
        results = []
        query_lower = query.lower()
        
        # Parse search query
        category_filter = ""
        if "category:" in query_lower:
            parts = query_lower.split("category:")
            query_lower = parts[0].strip()
            category_filter = parts[1].strip() if len(parts) > 1 else ""
            
        for page in self.search_index:
            score = 0
            
            # Category filter
            if category_filter and category_filter not in page.get("category", "").lower():
                continue
                
            # Search in title (higher weight)
            if query_lower in page.get("title", "").lower():
                score += 10
                
            # Search in description
            if query_lower in page.get("description", "").lower():
                score += 5
                
            # Search in content
            if query_lower in page.get("search_text", ""):
                score += 1
                
            # Search in tags
            for tag in page.get("tags", []):
                if query_lower in tag.lower():
                    score += 3
                    
            if score > 0:
                results.append((score, page))
                
        # Sort by score
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Show search results
        self.show_search_results(query, results[:20])  # Top 20 results
        
    def show_search_results(self, query: str, results: List[tuple]):
        """Display search results"""
        if not results:
            html = f"""
            <h1>Search Results</h1>
            <p>No results found for "<strong>{query}</strong>"</p>
            <p>Try:</p>
            <ul>
                <li>Different keywords</li>
                <li>Checking spelling</li>
                <li>Using the AI Assistant for help</li>
            </ul>
            """
        else:
            html = f"<h1>Search Results for '{query}'</h1>\n"
            html += f"<p>Found {len(results)} results:</p>\n<hr>\n"
            
            for score, page in results:
                title = page.get("title", "Untitled")
                description = page.get("description", "")
                path = page.get("path", "")
                category = page.get("category", "").title()
                
                html += f"""
                <div style="margin-bottom: 15px; padding: 10px; border-left: 3px solid #3498db;">
                    <h3><a href="{path}">{title}</a></h3>
                    <p style="color: #666; font-size: 12px;">📁 {category}</p>
                    <p>{description}</p>
                </div>
                """
                
        self.content_viewer.setHtml(html)
        self.breadcrumb.setText(f"🔍 Search Results for '{query}'")
        
    def on_internal_link(self, link: str):
        """Handle internal documentation links"""
        # Resolve relative links
        if not link.startswith('/') and self.current_page:
            current_dir = '/'.join(self.current_page.split('/')[:-1])
            if current_dir:
                link = f"{current_dir}/{link}"
                
        # Clean up the link
        link = link.replace('../', '').replace('./', '')
        
        if link in self.documentation.get("pages", {}):
            self.show_page(link)
        else:
            # Try to find similar page
            for page_path in self.documentation.get("pages", {}):
                if link in page_path:
                    self.show_page(page_path)
                    return
                    
            self.status_label.setText(f"Link not found: {link}")
            
    def go_back(self):
        """Navigate back to previous page"""
        if self.page_history:
            previous_page = self.page_history.pop()
            self.current_page = previous_page
            self.show_page(previous_page)
            
            if not self.page_history:
                self.back_btn.setEnabled(False)
                
    def print_page(self):
        """Print current page"""
        from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
        
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec_() == QPrintDialog.Accepted:
            self.content_viewer.print_(printer)
            
    def export_page(self):
        """Export current page"""
        from PyQt5.QtWidgets import QFileDialog
        
        if not self.current_page:
            return
            
        page_data = self.documentation["pages"][self.current_page]
        title = page_data.get("front_matter", {}).get("title", "document")
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Page", f"{title}.html", "HTML Files (*.html);;Text Files (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    if filename.endswith('.html'):
                        f.write(self.content_viewer.toHtml())
                    else:
                        f.write(self.content_viewer.toPlainText())
                        
                self.status_label.setText(f"Exported to {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Export Error", f"Failed to export: {e}")

# Context-sensitive help integration
class ContextHelpMixin:
    """Mixin to add context-sensitive help to any widget"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.help_context = ""
        
    def set_help_context(self, context: str):
        """Set help context for this widget"""
        self.help_context = context
        
    def show_context_help(self):
        """Show context-sensitive help"""
        if hasattr(self, 'parent') and hasattr(self.parent(), 'help_system'):
            help_system = self.parent().help_system
            if self.help_context:
                # Try to find relevant help page
                help_system.perform_search(self.help_context)
            else:
                help_system.show()

def integrate_help_system(main_window):
    """Integrate help system into main application window"""
    
    # Create help system widget
    help_system = HelpSystemWidget()
    
    # Add to main window as hidden widget
    main_window.help_system = help_system
    
    # Modify show_help method to use new help system
    def enhanced_show_help():
        """Enhanced help function"""
        # Create help dialog
        dialog = QDialog(main_window)
        dialog.setWindowTitle("Help & Documentation")
        dialog.setModal(False)
        dialog.resize(1000, 700)
        
        layout = QVBoxLayout()
        layout.addWidget(help_system)
        
        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        dialog.show()
        
    # Replace original show_help method
    main_window.show_help = enhanced_show_help
    
    return help_system

if __name__ == "__main__":
    # Test the help system standalone
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    help_widget = HelpSystemWidget("docs")
    help_widget.show()
    
    sys.exit(app.exec_())