"""
Enhanced Weather Widget for Westfall Assistant
Phase 6 implementation with workspace environment recommendations
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor

# Optional dependencies with fallbacks
try:
    from util.app_theme import AppTheme
    HAS_THEME = True
except ImportError:
    HAS_THEME = False
    class AppTheme:
        BACKGROUND = "#000000"
        SECONDARY_BG = "#1a1a1a"
        PRIMARY_COLOR = "#ff0000"
        TEXT_PRIMARY = "#ffffff"
        TEXT_SECONDARY = "#cccccc"

try:
    from util.error_handler import get_error_handler
    HAS_ERROR_HANDLER = True
except ImportError:
    HAS_ERROR_HANDLER = False

try:
    from security.api_key_vault import APIKeyVault
    HAS_API_VAULT = True
except ImportError:
    HAS_API_VAULT = False


class WeatherWidget(QWidget):
    """Enhanced weather widget with workspace recommendations"""
    
    def __init__(self):
        super().__init__()
        self.api_key = None
        self.current_location = None
        self.weather_data = None
        self.forecast_data = None
        self.settings_file = "data/weather_settings.json"
        
        # Error handler
        self.error_handler = get_error_handler(self) if HAS_ERROR_HANDLER else None
        
        # Initialize data directory
        os.makedirs('data', exist_ok=True)
        
        # Load settings
        self.load_settings()
        
        # Get API key
        self.get_api_key()
        
        # Initialize UI
        self.init_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_weather)
        self.update_timer.start(900000)  # Update every 15 minutes
        
        # Initial weather fetch
        if self.api_key and self.current_location:
            self.refresh_weather()

    def load_settings(self):
        """Load weather settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.current_location = settings.get('location')
                    self.temperature_unit = settings.get('temperature_unit', 'metric')
                    self.show_forecast = settings.get('show_forecast', True)
                    self.show_recommendations = settings.get('show_recommendations', True)
            else:
                # Default settings
                self.current_location = None
                self.temperature_unit = 'metric'
                self.show_forecast = True
                self.show_recommendations = True
        except Exception as e:
            print(f"Error loading weather settings: {e}")

    def save_settings(self):
        """Save weather settings to file"""
        try:
            settings = {
                'location': self.current_location,
                'temperature_unit': self.temperature_unit,
                'show_forecast': self.show_forecast,
                'show_recommendations': self.show_recommendations
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving weather settings: {e}")

    def get_api_key(self):
        """Get API key from secure vault or prompt user"""
        # Try secure vault first
        if HAS_API_VAULT:
            try:
                vault = APIKeyVault()
                key = vault.get_key('openweathermap')
                if key:
                    self.api_key = key
                    return
            except:
                pass
        
        # Try environment variable
        key = os.getenv('OPENWEATHER_API_KEY')
        if key:
            self.api_key = key
            return
        
        # Check if we have a demo key or suggest getting one
        self.api_key = None

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Apply theme
        if HAS_THEME:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {AppTheme.BACKGROUND};
                    color: {AppTheme.TEXT_PRIMARY};
                }}
                QGroupBox {{
                    border: 2px solid {AppTheme.PRIMARY_COLOR};
                    border-radius: 8px;
                    margin-top: 10px;
                    font-weight: bold;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }}
            """)
        
        # Header with location selection
        header = self.create_header()
        layout.addWidget(header)
        
        # Current weather display
        self.current_weather_widget = self.create_current_weather_widget()
        layout.addWidget(self.current_weather_widget)
        
        # Forecast display
        self.forecast_widget = self.create_forecast_widget()
        layout.addWidget(self.forecast_widget)
        
        # Workspace recommendations
        self.recommendations_widget = self.create_recommendations_widget()
        layout.addWidget(self.recommendations_widget)
        
        # Settings panel
        settings_widget = self.create_settings_widget()
        layout.addWidget(settings_widget)

    def create_header(self):
        """Create the header with location and refresh controls"""
        header_widget = QWidget()
        if HAS_THEME:
            header_widget.setStyleSheet(f"""
                background-color: {AppTheme.SECONDARY_BG}; 
                border-bottom: 2px solid {AppTheme.PRIMARY_COLOR};
                padding: 10px;
            """)
        
        layout = QHBoxLayout(header_widget)
        
        # Title
        title_label = QLabel("🌤️ Weather & Environment")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        if HAS_THEME:
            title_label.setStyleSheet(f"color: {AppTheme.PRIMARY_COLOR};")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Location input
        layout.addWidget(QLabel("Location:"))
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Enter city name or coordinates")
        self.location_input.setMinimumWidth(200)
        if self.current_location:
            self.location_input.setText(self.current_location)
        layout.addWidget(self.location_input)
        
        # Set location button
        set_location_btn = QPushButton("📍 Set Location")
        set_location_btn.clicked.connect(self.set_location)
        layout.addWidget(set_location_btn)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_weather)
        layout.addWidget(refresh_btn)
        
        return header_widget

    def create_current_weather_widget(self):
        """Create current weather display"""
        group = QGroupBox("Current Weather")
        layout = QHBoxLayout(group)
        
        # Weather icon and main info
        main_info_layout = QVBoxLayout()
        
        self.weather_icon_label = QLabel("🌤️")
        self.weather_icon_label.setAlignment(Qt.AlignCenter)
        self.weather_icon_label.setFont(QFont("Arial", 48))
        main_info_layout.addWidget(self.weather_icon_label)
        
        self.temperature_label = QLabel("--°")
        self.temperature_label.setAlignment(Qt.AlignCenter)
        temp_font = QFont()
        temp_font.setPointSize(36)
        temp_font.setBold(True)
        self.temperature_label.setFont(temp_font)
        if HAS_THEME:
            self.temperature_label.setStyleSheet(f"color: {AppTheme.PRIMARY_COLOR};")
        main_info_layout.addWidget(self.temperature_label)
        
        self.description_label = QLabel("--")
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setFont(QFont("Arial", 12))
        main_info_layout.addWidget(self.description_label)
        
        layout.addLayout(main_info_layout)
        
        # Additional details
        details_layout = QVBoxLayout()
        
        self.feels_like_label = QLabel("Feels like: --°")
        self.humidity_label = QLabel("Humidity: --%")
        self.pressure_label = QLabel("Pressure: -- hPa")
        self.wind_label = QLabel("Wind: -- m/s")
        self.visibility_label = QLabel("Visibility: -- km")
        self.uv_index_label = QLabel("UV Index: --")
        
        for label in [self.feels_like_label, self.humidity_label, self.pressure_label,
                      self.wind_label, self.visibility_label, self.uv_index_label]:
            label.setFont(QFont("Arial", 10))
            if HAS_THEME:
                label.setStyleSheet(f"color: {AppTheme.TEXT_SECONDARY};")
            details_layout.addWidget(label)
        
        layout.addLayout(details_layout)
        
        return group

    def create_forecast_widget(self):
        """Create forecast display"""
        group = QGroupBox("5-Day Forecast")
        layout = QHBoxLayout(group)
        
        # Create forecast day widgets
        self.forecast_day_widgets = []
        for i in range(5):
            day_widget = self.create_forecast_day_widget()
            self.forecast_day_widgets.append(day_widget)
            layout.addWidget(day_widget)
        
        return group

    def create_forecast_day_widget(self):
        """Create a single forecast day widget"""
        widget = QWidget()
        widget.setMinimumWidth(120)
        layout = QVBoxLayout(widget)
        
        # Day label
        day_label = QLabel("---")
        day_label.setAlignment(Qt.AlignCenter)
        day_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(day_label)
        
        # Weather icon
        icon_label = QLabel("🌤️")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFont(QFont("Arial", 24))
        layout.addWidget(icon_label)
        
        # Temperature range
        temp_label = QLabel("--° / --°")
        temp_label.setAlignment(Qt.AlignCenter)
        temp_label.setFont(QFont("Arial", 10))
        layout.addWidget(temp_label)
        
        # Description
        desc_label = QLabel("---")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setFont(QFont("Arial", 8))
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Store references
        widget.day_label = day_label
        widget.icon_label = icon_label
        widget.temp_label = temp_label
        widget.desc_label = desc_label
        
        if HAS_THEME:
            widget.setStyleSheet(f"""
                QWidget {{
                    border: 1px solid {AppTheme.PRIMARY_COLOR};
                    border-radius: 5px;
                    margin: 2px;
                    padding: 5px;
                }}
            """)
        
        return widget

    def create_recommendations_widget(self):
        """Create workspace environment recommendations"""
        group = QGroupBox("Workspace Recommendations")
        layout = QVBoxLayout(group)
        
        # Recommendations list
        self.recommendations_list = QListWidget()
        self.recommendations_list.setMaximumHeight(150)
        if HAS_THEME:
            self.recommendations_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {AppTheme.SECONDARY_BG};
                    color: {AppTheme.TEXT_PRIMARY};
                    border: 1px solid {AppTheme.PRIMARY_COLOR};
                }}
            """)
        layout.addWidget(self.recommendations_list)
        
        return group

    def create_settings_widget(self):
        """Create settings panel"""
        group = QGroupBox("Settings")
        layout = QHBoxLayout(group)
        
        # Temperature unit
        layout.addWidget(QLabel("Temperature:"))
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Celsius (°C)", "Fahrenheit (°F)", "Kelvin (K)"])
        self.unit_combo.setCurrentIndex(0 if self.temperature_unit == 'metric' else 1)
        self.unit_combo.currentTextChanged.connect(self.change_temperature_unit)
        layout.addWidget(self.unit_combo)
        
        layout.addStretch()
        
        # Show forecast checkbox
        self.forecast_checkbox = QCheckBox("Show Forecast")
        self.forecast_checkbox.setChecked(self.show_forecast)
        self.forecast_checkbox.toggled.connect(self.toggle_forecast)
        layout.addWidget(self.forecast_checkbox)
        
        # Show recommendations checkbox
        self.recommendations_checkbox = QCheckBox("Show Recommendations")
        self.recommendations_checkbox.setChecked(self.show_recommendations)
        self.recommendations_checkbox.toggled.connect(self.toggle_recommendations)
        layout.addWidget(self.recommendations_checkbox)
        
        # API key button
        api_key_btn = QPushButton("🔑 Set API Key")
        api_key_btn.clicked.connect(self.prompt_for_api_key)
        layout.addWidget(api_key_btn)
        
        return group

    def set_location(self):
        """Set the current location"""
        location = self.location_input.text().strip()
        if location:
            self.current_location = location
            self.save_settings()
            self.refresh_weather()

    def change_temperature_unit(self, unit_text):
        """Change temperature unit"""
        if "Celsius" in unit_text:
            self.temperature_unit = "metric"
        elif "Fahrenheit" in unit_text:
            self.temperature_unit = "imperial"
        else:
            self.temperature_unit = "kelvin"
        
        self.save_settings()
        if self.weather_data:
            self.update_weather_display()

    def toggle_forecast(self, checked):
        """Toggle forecast visibility"""
        self.show_forecast = checked
        self.forecast_widget.setVisible(checked)
        self.save_settings()

    def toggle_recommendations(self, checked):
        """Toggle recommendations visibility"""
        self.show_recommendations = checked
        self.recommendations_widget.setVisible(checked)
        self.save_settings()

    def prompt_for_api_key(self):
        """Prompt user to enter API key"""
        dialog = QDialog(self)
        dialog.setWindowTitle("OpenWeatherMap API Key")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        info_label = QLabel(
            "To use weather features, you need an OpenWeatherMap API key.\n\n"
            "Get one free at: https://openweathermap.org/api\n\n"
            "Enter your API key below:"
        )
        layout.addWidget(info_label)
        
        api_key_input = QLineEdit()
        api_key_input.setPlaceholderText("Enter API key here...")
        api_key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(api_key_input)
        
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Key")
        save_btn.clicked.connect(lambda: self.save_api_key(api_key_input.text(), dialog))
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()

    def save_api_key(self, api_key, dialog):
        """Save API key to secure vault"""
        if not api_key.strip():
            QMessageBox.warning(dialog, "Invalid Key", "Please enter a valid API key.")
            return
        
        # Try to save to secure vault
        if HAS_API_VAULT:
            try:
                vault = APIKeyVault()
                vault.store_key('openweathermap', api_key.strip())
                self.api_key = api_key.strip()
                dialog.accept()
                QMessageBox.information(self, "API Key Saved", "API key saved securely!")
                return
            except Exception as e:
                print(f"Error saving to vault: {e}")
        
        # Fallback: just store in memory for this session
        self.api_key = api_key.strip()
        dialog.accept()
        QMessageBox.information(self, "API Key Set", "API key set for this session only.")

    def refresh_weather(self):
        """Refresh weather data"""
        if not self.api_key:
            self.prompt_for_api_key()
            return
        
        if not self.current_location:
            QMessageBox.warning(self, "No Location", "Please set a location first.")
            return
        
        # Start weather fetch in background
        self.weather_thread = WeatherFetchThread(self.api_key, self.current_location, self.temperature_unit)
        self.weather_thread.weather_fetched.connect(self.on_weather_fetched)
        self.weather_thread.error_occurred.connect(self.on_weather_error)
        self.weather_thread.start()

    def on_weather_fetched(self, current_data, forecast_data):
        """Handle fetched weather data"""
        self.weather_data = current_data
        self.forecast_data = forecast_data
        self.update_weather_display()
        self.update_recommendations()

    def on_weather_error(self, error_message):
        """Handle weather fetch error"""
        if self.error_handler:
            self.error_handler.handle_network_error(Exception(error_message), 
                                                   "Failed to fetch weather data")
        else:
            QMessageBox.warning(self, "Weather Error", f"Failed to fetch weather: {error_message}")

    def update_weather_display(self):
        """Update the weather display with current data"""
        if not self.weather_data:
            return
        
        # Current weather
        temp = self.weather_data['main']['temp']
        unit_symbol = "°C" if self.temperature_unit == "metric" else "°F" if self.temperature_unit == "imperial" else "K"
        
        self.temperature_label.setText(f"{temp:.0f}{unit_symbol}")
        self.description_label.setText(self.weather_data['weather'][0]['description'].title())
        
        # Weather icon
        weather_main = self.weather_data['weather'][0]['main'].lower()
        icon = self.get_weather_icon(weather_main)
        self.weather_icon_label.setText(icon)
        
        # Details
        self.feels_like_label.setText(f"Feels like: {self.weather_data['main']['feels_like']:.0f}{unit_symbol}")
        self.humidity_label.setText(f"Humidity: {self.weather_data['main']['humidity']}%")
        self.pressure_label.setText(f"Pressure: {self.weather_data['main']['pressure']} hPa")
        self.wind_label.setText(f"Wind: {self.weather_data['wind']['speed']:.1f} m/s")
        
        if 'visibility' in self.weather_data:
            visibility = self.weather_data['visibility'] / 1000  # Convert to km
            self.visibility_label.setText(f"Visibility: {visibility:.1f} km")
        
        # Update forecast
        self.update_forecast_display()

    def update_forecast_display(self):
        """Update the forecast display"""
        if not self.forecast_data or not self.show_forecast:
            return
        
        for i, day_widget in enumerate(self.forecast_day_widgets):
            if i < len(self.forecast_data['list']):
                forecast_item = self.forecast_data['list'][i]
                
                # Day name
                forecast_date = datetime.fromtimestamp(forecast_item['dt'])
                day_name = forecast_date.strftime('%a')
                day_widget.day_label.setText(day_name)
                
                # Icon
                weather_main = forecast_item['weather'][0]['main'].lower()
                icon = self.get_weather_icon(weather_main)
                day_widget.icon_label.setText(icon)
                
                # Temperature range
                temp_min = forecast_item['main']['temp_min']
                temp_max = forecast_item['main']['temp_max']
                unit_symbol = "°C" if self.temperature_unit == "metric" else "°F" if self.temperature_unit == "imperial" else "K"
                day_widget.temp_label.setText(f"{temp_max:.0f}° / {temp_min:.0f}°")
                
                # Description
                description = forecast_item['weather'][0]['description'].title()
                day_widget.desc_label.setText(description)

    def get_weather_icon(self, weather_condition):
        """Get weather icon emoji based on condition"""
        icons = {
            'clear': '☀️',
            'clouds': '☁️',
            'rain': '🌧️',
            'snow': '🌨️',
            'thunderstorm': '⛈️',
            'drizzle': '🌦️',
            'mist': '🌫️',
            'fog': '🌫️',
            'haze': '🌫️'
        }
        return icons.get(weather_condition, '🌤️')

    def update_recommendations(self):
        """Update workspace environment recommendations"""
        if not self.weather_data or not self.show_recommendations:
            return
        
        self.recommendations_list.clear()
        recommendations = []
        
        # Temperature-based recommendations
        temp = self.weather_data['main']['temp']
        if self.temperature_unit == "imperial":
            if temp > 80:  # > 80°F
                recommendations.append("🌡️ High temperature - consider air conditioning for comfort")
            elif temp < 50:  # < 50°F
                recommendations.append("🧥 Low temperature - ensure adequate heating")
        else:  # Celsius
            if temp > 27:  # > 27°C
                recommendations.append("🌡️ High temperature - consider air conditioning for comfort")
                recommendations.append("💧 Stay hydrated and take regular breaks")
            elif temp < 10:  # < 10°C
                recommendations.append("🧥 Low temperature - ensure adequate heating")
                recommendations.append("☕ Consider warm beverages to stay comfortable")
        
        # Humidity-based recommendations
        humidity = self.weather_data['main']['humidity']
        if humidity > 70:
            recommendations.append("💨 High humidity - consider dehumidifier for better focus")
        elif humidity < 30:
            recommendations.append("💧 Low humidity - consider humidifier to prevent dry eyes")
        
        # Weather condition recommendations
        weather_main = self.weather_data['weather'][0]['main'].lower()
        if weather_main == 'rain':
            recommendations.append("🌧️ Rainy weather - great for indoor focused work")
            recommendations.append("☕ Perfect time for productivity with ambient rain sounds")
        elif weather_main == 'clear':
            recommendations.append("☀️ Clear weather - consider taking breaks outdoors")
            recommendations.append("🌱 Good day for outdoor meetings or walking meetings")
        elif weather_main == 'snow':
            recommendations.append("❄️ Snowy weather - ideal for cozy indoor work sessions")
        elif weather_main == 'thunderstorm':
            recommendations.append("⛈️ Thunderstorm - ensure UPS backup for electronics")
        
        # Wind-based recommendations
        if 'wind' in self.weather_data and self.weather_data['wind']['speed'] > 10:
            recommendations.append("💨 High winds - secure outdoor equipment")
        
        # UV Index recommendations (if available)
        if temp > 20 and weather_main == 'clear':
            recommendations.append("🕶️ Bright conditions - consider blinds to reduce screen glare")
        
        # Pressure-based recommendations
        pressure = self.weather_data['main']['pressure']
        if pressure < 1000:
            recommendations.append("📉 Low pressure - some people may feel less energetic")
        elif pressure > 1020:
            recommendations.append("📈 High pressure - typically good for concentration")
        
        # Add recommendations to list
        for recommendation in recommendations:
            self.recommendations_list.addItem(recommendation)
        
        # If no specific recommendations, add general ones
        if not recommendations:
            self.recommendations_list.addItem("✨ Weather conditions look good for productive work!")
            self.recommendations_list.addItem("🌿 Consider opening windows for fresh air if comfortable")


class WeatherFetchThread(QThread):
    """Thread for fetching weather data without blocking UI"""
    
    weather_fetched = pyqtSignal(dict, dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_key, location, units):
        super().__init__()
        self.api_key = api_key
        self.location = location
        self.units = units

    def run(self):
        """Fetch weather data in background thread"""
        try:
            # Current weather API call
            current_url = f"http://api.openweathermap.org/data/2.5/weather"
            current_params = {
                'q': self.location,
                'appid': self.api_key,
                'units': self.units
            }
            
            current_response = requests.get(current_url, params=current_params, timeout=10)
            current_response.raise_for_status()
            current_data = current_response.json()
            
            # Forecast API call
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast"
            forecast_params = {
                'q': self.location,
                'appid': self.api_key,
                'units': self.units,
                'cnt': 5  # 5 forecasts
            }
            
            forecast_response = requests.get(forecast_url, params=forecast_params, timeout=10)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            self.weather_fetched.emit(current_data, forecast_data)
            
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")


# Legacy WeatherWindow for compatibility
class WeatherWindow(QMainWindow):
    """Legacy weather window wrapper"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather & Environment")
        self.setMinimumSize(800, 600)
        
        # Use the new widget as central widget
        self.weather_widget = WeatherWidget()
        self.setCentralWidget(self.weather_widget)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    # Apply theme if available
    if HAS_THEME:
        AppTheme.apply_to_application()
    
    window = WeatherWindow()
    window.show()
    
    sys.exit(app.exec_())