import sys
import requests
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
import feedparser

class NewsWorker(QThread):
    news_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, source="bbc"):
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
            "bbc": "http://feeds.bbci.co.uk/news/rss.xml",
            "cnn": "http://rss.cnn.com/rss/cnn_topstories.rss",
            "reuters": "http://feeds.reuters.com/reuters/topNews"
        }
        
        feed_url = feeds.get(self.source, feeds["bbc"])
        feed = feedparser.parse(feed_url)
        
        articles = []
        for entry in feed.entries[:20]:
            article = {
                "title": entry.title,
                "description": entry.get("summary", ""),
                "url": entry.link,
                "publishedAt": entry.get("published", ""),
                "source": {"name": self.source.upper()}
            }
            articles.append(article)
        
        self.news_loaded.emit(articles)

class NewsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.articles = []
        self.init_ui()
        self.load_news()
    
    def init_ui(self):
        self.setWindowTitle("News Reader")
        self.setGeometry(100, 100, 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Source selector
        source_label = QLabel("Source:")
        toolbar.addWidget(source_label)
        
        self.source_combo = QComboBox()
        self.source_combo.addItems(["BBC", "CNN", "Reuters", "TechCrunch", "The Verge"])
        self.source_combo.currentTextChanged.connect(self.change_source)
        toolbar.addWidget(self.source_combo)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search news...")
        self.search_input.textChanged.connect(self.search_news)
        toolbar.addWidget(self.search_input)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_news)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # News list
        self.news_list = QListWidget()
        self.news_list.itemClicked.connect(self.show_article)
        layout.addWidget(self.news_list)
        
        # Article viewer
        self.article_viewer = QTextBrowser()
        self.article_viewer.setOpenExternalLinks(True)
        self.article_viewer.setMaximumHeight(200)
        layout.addWidget(self.article_viewer)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Loading news...")
    
    def load_news(self):
        self.news_list.clear()
        self.status_bar.showMessage("Loading news...")
        
        source = self.source_combo.currentText().lower()
        self.worker = NewsWorker(source)
        self.worker.news_loaded.connect(self.display_news)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()
    
    def display_news(self, articles):
        self.articles = articles
        for article in articles:
            item = QListWidgetItem()
            title = article.get('title', 'No title')
            source = article.get('source', {}).get('name', 'Unknown')
            published = article.get('publishedAt', '')
            
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    published = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            item.setText(f"{title}\n{source} - {published}")
            item.setData(Qt.UserRole, article)
            self.news_list.addItem(item)
        
        self.status_bar.showMessage(f"Loaded {len(articles)} articles")
    
    def show_article(self, item):
        article = item.data(Qt.UserRole)
        html = f"""
        <h2>{article.get('title', 'No title')}</h2>
        <p><b>Source:</b> {article.get('source', {}).get('name', 'Unknown')}</p>
        <p><b>Published:</b> {article.get('publishedAt', 'Unknown')}</p>
        <p>{article.get('description', 'No description available')}</p>
        <p><a href="{article.get('url', '#')}">Read full article</a></p>
        """
        self.article_viewer.setHtml(html)
    
    def search_news(self, text):
        for i in range(self.news_list.count()):
            item = self.news_list.item(i)
            article = item.data(Qt.UserRole)
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            
            if text.lower() in title or text.lower() in description:
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def change_source(self):
        self.load_news()
    
    def show_error(self, error):
        self.status_bar.showMessage(f"Error: {error}")
        QMessageBox.warning(self, "Error", f"Failed to load news: {error}")