"""Weather module using API vault for secure API key management."""

import requests


class WeatherService:
    """Weather service that uses the API vault for secure API key management."""
    
    def __init__(self):
        # In weather.py, replace the API key line with:
        from security.api_key_vault import APIKeyVault
        vault = APIKeyVault()
        api_key = vault.get_key('openweathermap', 'demo_key')
        
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    def get_weather(self, location="New York"):
        """Get weather data for a location."""
        if not self.api_key or self.api_key == 'demo_key':
            return {
                "status": "error",
                "message": "API key not configured. Please set up your OpenWeatherMap API key."
            }
        
        try:
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "status": "success",
                "location": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "condition": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"],
                "visibility": data.get("visibility", "N/A")
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Failed to fetch weather data: {str(e)}"
            }
        except KeyError as e:
            return {
                "status": "error", 
                "message": f"Unexpected response format: {str(e)}"
            }