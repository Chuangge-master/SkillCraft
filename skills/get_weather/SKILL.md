---
name: get_weather
description: Get current weather and temperature for a given city or latitude/longitude.
when_to_use: When you need to know the current weather and temperature in a specific location.
run_by_script: true
---

This skill uses the free Open-Meteo API to fetch real-time weather data.
It accepts a city name (e.g., "Beijing") or coordinates (e.g., "39.9042,116.4074").
The service is rate-limited but does not require an API key.