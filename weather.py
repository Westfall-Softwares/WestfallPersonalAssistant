import sys
import os
import requests
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime

# Import security for API keys
try:
    from security.api_key_vault import APIKeyVault
except ImportError:
    APIKeyVault = None

class WeatherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = self.get_api_key()
        self.init_ui()
        
    def get_api_key(self):
        """Get API key from secure vault or environment"""
        # Try secure vault first
        if APIKeyVault:
            try:
                vault = APIKeyVault()
                key = vault.get_key('openweathermap')
                if key:
                    return key
            except:
                pass
        
        # Try environment variable
        key = os.getenv('OPENWEATHER_API_KEY')
        if key:
            return key
        
        # Prompt user to add key
        return self.prompt_for_api_key()
    
    def prompt_for_api_key(self):
        """Prompt user to enter API key"""
        dialog = QDialog(self)
        dialog.setWindowTitle("OpenWeatherMap API Key Required")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        info_label = QLabel(
            "Please enter your OpenWeatherMap API key.\n"
            "You can get one free at: https://openweathermap.org/api"
        )
        layout.addWidget(info_label)
        
        key_input = QLineEdit()
        key_input.setPlaceholderText("Enter API key...")
        layout.addWidget(key_input)
        
        save_checkbox = QCheckBox("Save key securely for future use")
        save_checkbox.setChecked(True)
        layout.addWidget(save_checkbox)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            key = key_input.text().strip()
            if key and save_checkbox.isChecked() and APIKeyVault:
                try:
                    vault = APIKeyVault()
                    vault.set_key('openweathermap', key)
                except:
                    pass
            return key
        return None
    
    def init_ui(self):
        self.setWindowTitle("Weather")
        self.setGeometry(100, 100, 600, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add tooltip
        self.setToolTip("Check weather conditions and forecast")
        
        # Location input
        location_layout = QHBoxLayout()
        
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Enter city name...")
        self.location_input.setToolTip("Type a city name and press Enter or click Get Weather")
        self.location_input.returnPressed.connect(self.get_weather)
        location_layout.addWidget(self.location_input)
        
        get_weather_btn = QPushButton("Get Weather")
        get_weather_btn.setToolTip("Fetch current weather for the specified location")
        get_weather_btn.clicked.connect(self.get_weather)
        location_layout.addWidget(get_weather_btn)
        
        layout.addLayout(location_layout)
        
        # Current weather display
        self.current_weather_label = QLabel("Enter a location to get weather")
        self.current_weather_label.setAlignment(Qt.AlignCenter)
        self.current_weather_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                padding: 20px;
                background-color: #f0f0f0;
                border-radius: 10px;
                margin: 10px;
            }
        """)
        layout.addWidget(self.current_weather_label)
        
        # Forecast
        forecast_label = QLabel("5-Day Forecast:")
        forecast_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(forecast_label)
        
        self.forecast_layout = QVBoxLayout()
        layout.addLayout(self.forecast_layout)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_weather)
        self.refresh_timer.start(600000)  # Refresh every 10 minutes
    
    def get_weather(self):
        if not self.api_key:
            QMessageBox.warning(self, "API Key Required", 
                              "Please configure your OpenWeatherMap API key in Settings")
            return
            
        location = self.location_input.text()
        if not location:
            QMessageBox.warning(self, "Location Required", "Please enter a city name")
            return
        
        self.status_bar.showMessage("Fetching weather data...")
        
        try:
            # Current weather
            current_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.api_key}&units=metric"
            current_response = requests.get(current_url, timeout=10)
            
            if current_response.status_code == 200:
                current_data = current_response.json()
                self.display_current_weather(current_data)
                
                # Forecast
                forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={self.api_key}&units=metric"
                forecast_response = requests.get(forecast_url, timeout=10)
                
                if forecast_response.status_code == 200:
                    forecast_data = forecast_response.json()
                    self.display_forecast(forecast_data)
                
                self.status_bar.showMessage(f"Weather updated for {location}")
            else:
                error_msg = current_response.json().get('message', 'Unknown error')
                QMessageBox.warning(self, "Error", f"Failed to get weather: {error_msg}")
                self.status_bar.showMessage("Error fetching weather")
                
        except requests.RequestException as e:
            QMessageBox.warning(self, "Network Error", f"Failed to connect: {str(e)}")
            self.status_bar.showMessage("Network error")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
            self.status_bar.showMessage("Error")
    
    def display_current_weather(self, data):
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        description = data['weather'][0]['description'].title()
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        city = data['name']
        country = data['sys']['country']
        
        weather_text = f"""
        📍 {city}, {country}
        🌡️ Temperature: {temp:.1f}°C (Feels like {feels_like:.1f}°C)
        ☁️ {description}
        💧 Humidity: {humidity}%
        💨 Wind Speed: {wind_speed} m/s
        """
        
        self.current_weather_label.setText(weather_text)
    
    def display_forecast(self, data):
        # Clear previous forecast
        while self.forecast_layout.count():
            child = self.forecast_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Group forecast by day (show one per day at noon)
        daily_forecasts = {}
        for item in data['list']:
            date = datetime.fromtimestamp(item['dt']).date()
            time = datetime.fromtimestamp(item['dt']).hour
            
            # Prefer noon forecast, or take first available
            if date not in daily_forecasts or abs(time - 12) < abs(datetime.fromtimestamp(daily_forecasts[date]['dt']).hour - 12):
                daily_forecasts[date] = item
        
        # Display up to 5 days
        for date, forecast in list(daily_forecasts.items())[:5]:
            forecast_widget = QWidget()
            forecast_layout = QHBoxLayout(forecast_widget)
            
            date_label = QLabel(date.strftime("%A, %b %d"))
            date_label.setMinimumWidth(120)
            forecast_layout.addWidget(date_label)
            
            temp_label = QLabel(f"{forecast['main']['temp']:.1f}°C")
            forecast_layout.addWidget(temp_label)
            
            desc_label = QLabel(forecast['weather'][0]['description'].title())
            forecast_layout.addWidget(desc_label)
            
            forecast_layout.addStretch()
            
            self.forecast_layout.addWidget(forecast_widget)
    
    def refresh_weather(self):
        """Auto-refresh weather if location is set"""
        if self.location_input.text():
            self.get_weather()