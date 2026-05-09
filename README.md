# Travel Planner

## Deploy to Vercel without committing API keys

This project generates a static site into `output/`.

1. Do not commit `.env` or `output/`.
2. In Vercel, add an Environment Variable:

```text
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

3. Keep your Google Maps key restricted to your production domains, for example:

```text
https://travel-planner-lac-five.vercel.app/*
https://*.vercel.app/*
http://127.0.0.1:8000/*
http://localhost:8000/*
```

4. Vercel runs `python3 generate_travel_viz.py` during build and serves the generated `output/index.html`.

Important: Google Maps JavaScript API browser keys are visible in browser network requests by design. The safe pattern is to keep the key out of GitHub and restrict it by HTTP referrer in Google Cloud.
