# components/weather_component.py
from src.base_component import BaseComponent


class WeatherComponent(BaseComponent):
    def __init__(self, name: str):
        super().__init__(name)

    def onload(self):
        print(f"WeatherComponent '{self.name}' is ready to provide weather.")

    def use(self, city: str) -> str:
        """
        Gets the current weather for a requested city.
        Args:
            city: The name of the city.
        Returns:
            A string with the current weather conditions for the city.
        """
        city_lower = city.lower()
        weather_data = {
            "london": "Partly cloudy, 15°C",
            "paris": "Sunny, 20°C",
            "new york": "Cloudy, 10°C, chance of rain",
            "tokyo": "Clear, 25°C",
            "mumbai": "Humid, 30°C, light breeze",
        }
        weather = weather_data.get(
            city_lower, "Weather data not available for this city."
        )
        return f"Current weather in {city}: {weather}"

    def destroy(self):
        print(f"WeatherComponent '{self.name}' destroyed.")
