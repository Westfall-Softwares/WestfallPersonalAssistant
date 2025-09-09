"""
WestfallPersonalAssistant Centralized Theme
Provides consistent styling across the application
"""

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

class AppTheme:
    """Centralized theme configuration"""
    
    # Primary colors
    BACKGROUND = "#000000"
    SECONDARY_BG = "#1a1a1a"
    TERTIARY_BG = "#2a2a2a"
    PRIMARY_COLOR = "#ff0000"
    SECONDARY_COLOR = "#cc0000"
    HIGHLIGHT_COLOR = "#ff3333"
    
    # Text colors
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#cccccc"
    TEXT_DISABLED = "#666666"
    TEXT_ACCENT = "#ff0000"
    
    # Border colors
    BORDER_COLOR = "#ff0000"
    BORDER_LIGHT = "#ff3333"
    BORDER_DARK = "#990000"
    
    # Status colors
    SUCCESS_COLOR = "#00cc00"
    WARNING_COLOR = "#ffcc00"
    ERROR_COLOR = "#ff0000"
    INFO_COLOR = "#0099ff"
    
    # Dimensions
    PADDING_SMALL = 5
    PADDING_MEDIUM = 10
    PADDING_LARGE = 20
    BORDER_RADIUS = 5
    BORDER_WIDTH = 1
    
    # Font sizes
    FONT_SMALL = 12
    FONT_MEDIUM = 14
    FONT_LARGE = 16
    FONT_XLARGE = 20
    FONT_HEADER = 24
    
    @staticmethod
    def get_button_style(primary=True, size="medium"):
        """Get consistent button styling"""
        bg_color = AppTheme.PRIMARY_COLOR if primary else AppTheme.SECONDARY_BG
        hover_color = AppTheme.SECONDARY_COLOR if primary else AppTheme.TERTIARY_BG
        
        padding = {
            "small": f"{AppTheme.PADDING_SMALL}px {AppTheme.PADDING_SMALL * 2}px",
            "medium": f"{AppTheme.PADDING_MEDIUM}px {AppTheme.PADDING_MEDIUM * 2}px",
            "large": f"{AppTheme.PADDING_LARGE}px {AppTheme.PADDING_LARGE * 2}px"
        }.get(size, f"{AppTheme.PADDING_MEDIUM}px {AppTheme.PADDING_MEDIUM * 2}px")
        
        font_size = {
            "small": AppTheme.FONT_SMALL,
            "medium": AppTheme.FONT_MEDIUM, 
            "large": AppTheme.FONT_LARGE
        }.get(size, AppTheme.FONT_MEDIUM)
        
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {AppTheme.TEXT_PRIMARY};
                border: none;
                padding: {padding};
                font-size: {font_size}px;
                font-weight: bold;
                border-radius: {AppTheme.BORDER_RADIUS}px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {AppTheme.BORDER_DARK};
            }}
            QPushButton:disabled {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def get_input_style():
        """Get consistent input styling"""
        return f"""
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                padding: {AppTheme.PADDING_MEDIUM}px;
                font-size: {AppTheme.FONT_MEDIUM}px;
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.HIGHLIGHT_COLOR};
            }}
            QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
                background-color: {AppTheme.TERTIARY_BG};
                color: {AppTheme.TEXT_DISABLED};
                border-color: {AppTheme.SECONDARY_BG};
            }}
        """
    
    @staticmethod
    def get_table_style():
        """Get consistent table styling"""
        return f"""
            QTableWidget {{
                background-color: {AppTheme.SECONDARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                gridline-color: #444444;
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
            }}
            QTableWidget::item {{
                padding: {AppTheme.PADDING_SMALL}px;
            }}
            QTableWidget::item:selected {{
                background-color: {AppTheme.PRIMARY_COLOR};
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {AppTheme.TERTIARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                padding: {AppTheme.PADDING_SMALL}px;
                border: 1px solid #444444;
                font-weight: bold;
            }}
        """
    
    @staticmethod
    def get_tab_style():
        """Get consistent tab styling"""
        return f"""
            QTabWidget::pane {{
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                background-color: {AppTheme.SECONDARY_BG};
                border-radius: {AppTheme.BORDER_RADIUS}px;
            }}
            QTabBar::tab {{
                background-color: {AppTheme.TERTIARY_BG};
                color: {AppTheme.TEXT_PRIMARY};
                padding: {AppTheme.PADDING_MEDIUM}px {AppTheme.PADDING_LARGE}px;
                margin-right: 2px;
                border-top-left-radius: {AppTheme.BORDER_RADIUS}px;
                border-top-right-radius: {AppTheme.BORDER_RADIUS}px;
            }}
            QTabBar::tab:selected {{
                background-color: {AppTheme.PRIMARY_COLOR};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {AppTheme.SECONDARY_COLOR};
            }}
        """
    
    @staticmethod
    def get_group_box_style():
        """Get consistent group box styling"""
        return f"""
            QGroupBox {{
                color: {AppTheme.TEXT_PRIMARY};
                border: {AppTheme.BORDER_WIDTH}px solid {AppTheme.BORDER_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                margin-top: 20px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {AppTheme.TEXT_ACCENT};
            }}
        """
    
    @staticmethod
    def get_scrollbar_style():
        """Get consistent scrollbar styling"""
        return f"""
            QScrollBar:vertical {{
                background-color: {AppTheme.SECONDARY_BG};
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #666666;
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {AppTheme.PRIMARY_COLOR};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background-color: {AppTheme.SECONDARY_BG};
                height: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: #666666;
                min-width: 20px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {AppTheme.PRIMARY_COLOR};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """
    
    @staticmethod
    def get_message_styles():
        """Get styles for different message types"""
        return {
            "success": f"""
                background-color: #003300;
                color: {AppTheme.SUCCESS_COLOR};
                border: 1px solid {AppTheme.SUCCESS_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                padding: 10px;
            """,
            "warning": f"""
                background-color: #332200;
                color: {AppTheme.WARNING_COLOR};
                border: 1px solid {AppTheme.WARNING_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                padding: 10px;
            """,
            "error": f"""
                background-color: #330000;
                color: {AppTheme.ERROR_COLOR};
                border: 1px solid {AppTheme.ERROR_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                padding: 10px;
            """,
            "info": f"""
                background-color: #002233;
                color: {AppTheme.INFO_COLOR};
                border: 1px solid {AppTheme.INFO_COLOR};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                padding: 10px;
            """
        }
    
    @staticmethod
    def get_complete_stylesheet():
        """Get complete application stylesheet"""
        styles = [
            f"QWidget {{ background-color: {AppTheme.BACKGROUND}; color: {AppTheme.TEXT_PRIMARY}; }}",
            f"QLabel {{ color: {AppTheme.TEXT_PRIMARY}; font-size: {AppTheme.FONT_MEDIUM}px; }}",
            f"QLabel#header {{ color: {AppTheme.TEXT_ACCENT}; font-size: {AppTheme.FONT_HEADER}px; font-weight: bold; }}",
            AppTheme.get_button_style(),
            AppTheme.get_input_style(),
            AppTheme.get_table_style(),
            AppTheme.get_tab_style(),
            AppTheme.get_group_box_style(),
            AppTheme.get_scrollbar_style()
        ]
        return "\n".join(styles)
    
    @staticmethod
    def apply_to_application():
        """Apply theme to entire application"""
        app = QApplication.instance()
        if not app:
            return False
        
        # Create dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(AppTheme.BACKGROUND))
        palette.setColor(QPalette.WindowText, QColor(AppTheme.TEXT_PRIMARY))
        palette.setColor(QPalette.Base, QColor(AppTheme.SECONDARY_BG))
        palette.setColor(QPalette.AlternateBase, QColor(AppTheme.TERTIARY_BG))
        palette.setColor(QPalette.ToolTipBase, QColor(AppTheme.TERTIARY_BG))
        palette.setColor(QPalette.ToolTipText, QColor(AppTheme.TEXT_PRIMARY))
        palette.setColor(QPalette.Text, QColor(AppTheme.TEXT_PRIMARY))
        palette.setColor(QPalette.Button, QColor(AppTheme.SECONDARY_BG))
        palette.setColor(QPalette.ButtonText, QColor(AppTheme.TEXT_PRIMARY))
        palette.setColor(QPalette.BrightText, QColor(AppTheme.PRIMARY_COLOR))
        palette.setColor(QPalette.Link, QColor(AppTheme.PRIMARY_COLOR))
        palette.setColor(QPalette.Highlight, QColor(AppTheme.PRIMARY_COLOR))
        palette.setColor(QPalette.HighlightedText, QColor(AppTheme.TEXT_PRIMARY))
        
        app.setPalette(palette)
        app.setStyleSheet(AppTheme.get_complete_stylesheet())
        return True