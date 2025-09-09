import sys
import os
import requests
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QPixmap, QPalette, QColor
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import feedparser
from urllib.parse import urlparse

class NewsImageLoader(QThread):
    image_loaded = pyqtSignal(str, QPixmap)
    
    def __init__(self, url, article_id):
        super().__init__()
        self.url = url
        self.article_id = article_id
    
    def run(self):
        try:
            response = requests.get(self.url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.image_loaded.emit(self.article_id, pixmap)
        except:
            pass

class NewsCard(QFrame):
    """Modern news card with image"""
    
    def __init__(self, article, parent=None):
        super().__init__(parent)
        self.article = article
        self.init_ui()
        self.load_image()
    
    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #ff0000;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
            QFrame:hover {
                background-color: #2a2a2a;
                border-color: #ff3333;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QHBoxLayout()
        
        # Image placeholder
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 100)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #333333;
                border: 1px solid #ff0000;
                border-radius: 5px;
            }
        """)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("📰")
        layout.addWidget(self.image_label)
        
        # Content area
        content_layout = QVBoxLayout()
        
        # Title
        title = QLabel(self.article.get('title', 'No title'))
        title.setWordWrap(True)
        title.setStyleSheet("""
            QLabel {
                color: #ff0000;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        content_layout.addWidget(title)
        
        # Source and date
        source = self.article.get('source', {}).get('name', 'Unknown')
        published = self.article.get('publishedAt', '')
        if published:
            try:
                dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                published = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        meta = QLabel(f"📍 {source} • 🕐 {published}")
        meta.setStyleSheet("color: #888888; font-size: 12px;")
        content_layout.addWidget(meta)
        
        # Description
        description = self.article.get('description', 'No description available')
        desc_label = QLabel(description[:200] + "..." if len(description) > 200 else description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #cccccc; font-size: 14px;")
        content_layout.addWidget(desc_label)
        
        # Read more button
        read_btn = QPushButton("Read Full Article →")
        read_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                padding: 8px 15px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        read_btn.clicked.connect(self.open_article)
        content_layout.addWidget(read_btn, alignment=Qt.AlignRight)
        
        content_layout.addStretch()
        layout.addLayout(content_layout)
        
        self.setLayout(layout)
    
    def load_image(self):
        """Load article image"""
        image_url = self.article.get('urlToImage')
        if image_url:
            loader = NewsImageLoader(image_url, str(id(self)))
            loader.image_loaded.connect(self.set_image)
            loader.start()
    
    def set_image(self, article_id, pixmap):
        """Set loaded image"""
        if str(id(self)) == article_id:
            scaled = pixmap.scaled(150, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
    
    def open_article(self):
        """Open article in browser"""
        url = self.article.get('url')
        if url:
            from PyQt5.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl(url))

class NewsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.articles = []
        self.init_ui()
        self.apply_theme()
        self.load_news()
    
    def init_ui(self):
        self.setWindowTitle("News Reader")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📰 Latest News")
        title.setStyleSheet("""
            QLabel {
                color: #ff0000;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Source selector
        self.source_combo = QComboBox()
        self.source_combo.addItems(["All", "BBC", "CNN", "Reuters", "TechCrunch", "The Verge", "Bloomberg"])
        self.source_combo.setStyleSheet("""
            QComboBox {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #ff0000;
                padding: 8px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ff0000;
            }
        """)
        self.source_combo.currentTextChanged.connect(self.filter_news)
        header_layout.addWidget(self.source_combo)
        
        # Category selector
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Business", "Technology", "Sports", "Entertainment", "Health", "Science"])
        self.category_combo.setStyleSheet(self.source_combo.styleSheet())
        self.category_combo.currentTextChanged.connect(self.filter_news)
        header_layout.addWidget(self.category_combo)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        refresh_btn.clicked.connect(self.load_news)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search news...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #ff0000;
                padding: 10px;
                font-size: 14px;
            }
        """)
        self.search_input.textChanged.connect(self.search_news)
        layout.addWidget(self.search_input)
        
        # News cards area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #000000;
                border: none;
            }
        """)
        
        self.news_container = QWidget()
        self.news_layout = QVBoxLayout(self.news_container)
        self.news_layout.setSpacing(15)
        
        self.scroll_area.setWidget(self.news_container)
        layout.addWidget(self.scroll_area)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1a1a1a;
                color: #ff0000;
            }
        """)
    
    def apply_theme(self):
        """Apply black and red theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QWidget {
                background-color: #000000;
                color: white;
            }
        """)
    
    def load_news(self):
        """Load news from API or RSS"""
        self.status_bar.showMessage("Loading news...")
        
        # Clear existing news
        for i in reversed(range(self.news_layout.count())): 
            self.news_layout.itemAt(i).widget().setParent(None)
        
        # Try NewsAPI first
        try:
            api_key = None
            
            # Try environment variable first
            api_key = os.getenv('NEWSAPI_KEY')
            
            # Fall back to secure vault
            if not api_key:
                try:
                    from security.api_key_vault import APIKeyVault
                    vault = APIKeyVault()
                    api_key = vault.get_key('newsapi')
                except:
                    pass
            
            if api_key:
                url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    self.articles = data.get('articles', [])
                    self.display_news()
                    return
        except:
            pass
        
        # Fallback to RSS
        self.load_rss_news()
    
    def load_rss_news(self):
        """Load news from RSS feeds"""
        feeds = {
            "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
            "CNN": "http://rss.cnn.com/rss/cnn_topstories.rss",
            "Reuters": "http://feeds.reuters.com/reuters/topNews"
        }
        
        self.articles = []
        
        for source, feed_url in feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:  # Get 5 from each source
                    article = {
                        "title": entry.title,
                        "description": entry.get("summary", ""),
                        "url": entry.link,
                        "publishedAt": entry.get("published", ""),
                        "source": {"name": source},
                        "urlToImage": self.extract_image_from_entry(entry)
                    }
                    self.articles.append(article)
            except:
                continue
        
        self.display_news()
    
    def extract_image_from_entry(self, entry):
        """Try to extract image URL from RSS entry"""
        # Check for media content
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if 'image' in media.get('type', ''):
                    return media.get('url')
        
        # Check for enclosures
        if hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                if 'image' in enclosure.get('type', ''):
                    return enclosure.get('href')
        
        # Return None if no image found
        return None
    
    def display_news(self):
        """Display news articles as cards"""
        if not self.articles:
            no_news = QLabel("No news articles available")
            no_news.setAlignment(Qt.AlignCenter)
            no_news.setStyleSheet("color: #888888; font-size: 18px; padding: 50px;")
            self.news_layout.addWidget(no_news)
            self.status_bar.showMessage("No articles found")
            return
        
        for article in self.articles:
            card = NewsCard(article)
            self.news_layout.addWidget(card)
        
        self.news_layout.addStretch()
        self.status_bar.showMessage(f"Loaded {len(self.articles)} articles")
    
    def search_news(self, query):
        """Search news articles"""
        if not query:
            self.display_news()
            return
        
        # Clear existing display
        for i in reversed(range(self.news_layout.count())): 
            self.news_layout.itemAt(i).widget().setParent(None)
        
        # Filter articles
        filtered_articles = []
        query_lower = query.lower()
        
        for article in self.articles:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            source = article.get('source', {}).get('name', '').lower()
            
            if (query_lower in title or 
                query_lower in description or 
                query_lower in source):
                filtered_articles.append(article)
        
        # Display filtered articles
        if filtered_articles:
            for article in filtered_articles:
                card = NewsCard(article)
                self.news_layout.addWidget(card)
            self.news_layout.addStretch()
            self.status_bar.showMessage(f"Found {len(filtered_articles)} articles matching '{query}'")
        else:
            no_results = QLabel(f"No articles found matching '{query}'")
            no_results.setAlignment(Qt.AlignCenter)
            no_results.setStyleSheet("color: #888888; font-size: 18px; padding: 50px;")
            self.news_layout.addWidget(no_results)
            self.status_bar.showMessage("No results found")
    
    def filter_news(self):
        """Filter news by source and category"""
        source_filter = self.source_combo.currentText()
        category_filter = self.category_combo.currentText()
        
        # For now, just reload news - in a real implementation you'd filter the existing articles
        # This is a simplified version - the full implementation would filter by source and category
        self.display_news()

# Create worker thread for background news loading
class NewsWorker(QThread):
    news_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, source="all"):
        super().__init__()
        self.source = source
    
    def run(self):
        try:
            # Try NewsAPI first
            api_key = self.get_api_key()
            if api_key:
                self.fetch_newsapi(api_key)
            else:
                # Fallback to RSS feeds
                self.fetch_rss()
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def get_api_key(self):
        try:
            # Try environment variable first
            api_key = os.getenv('NEWSAPI_KEY')
            if api_key:
                return api_key
            
            # Fall back to secure vault
            from security.api_key_vault import APIKeyVault
            vault = APIKeyVault()
            return vault.get_key('newsapi')
        except:
            return None
    
    def fetch_newsapi(self, api_key):
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            self.news_loaded.emit(articles)
        else:
            self.fetch_rss()  # Fallback to RSS
    
    def fetch_rss(self):
        feeds = {
            "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
            "CNN": "http://rss.cnn.com/rss/cnn_topstories.rss",
            "Reuters": "http://feeds.reuters.com/reuters/topNews"
        }
        
        articles = []
        
        for source, feed_url in feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:  # Get 10 from each source
                    article = {
                        "title": entry.title,
                        "description": entry.get("summary", ""),
                        "url": entry.link,
                        "publishedAt": entry.get("published", ""),
                        "source": {"name": source},
                        "urlToImage": None  # RSS doesn't typically have images
                    }
                    articles.append(article)
            except:
                continue
        
        self.news_loaded.emit(articles)

def main():
    app = QApplication(sys.argv)
    window = NewsWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()