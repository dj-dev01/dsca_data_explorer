# dsca_explorer/config.py

HIFLD_BASE_URL = "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services?f=pjson"
HIFLD_HEADERS = {
    "User-Agent": "DSCA-Explorer (your.email@yourdomain.com)"
}
NOAA_BASE = "https://api.weather.gov"
NOAA_HEADERS = {
    "User-Agent": "DSCA-Explorer (your.email@yourdomain.com)"
}
USGS_HANS_BASE = "https://volcanoes.usgs.gov/hans-public/api"
USGS_GEOJSON = "https://volcanoes.usgs.gov/hans-public/map/geojson.php"
USGS_EQ_BASE = "https://earthquake.usgs.gov/fdsnws/event/1/query"
USGS_WATER_BASE = "https://waterservices.usgs.gov/nwis/iv/"
EPA_BASE = "https://enviro.epa.gov/enviro/efservice"
NASA_CMR = "https://cmr.earthdata.nasa.gov/search/collections.json"

CACHE_FILE = "dsca_layer_cache.json"

DOC_URLS = {
    "USGS Earthquake": "https://earthquake.usgs.gov/fdsnws/event/1/",
    "USGS Water Site": "https://waterservices.usgs.gov/docs/",
    "USGS Elevated Volcano": "https://volcanoes.usgs.gov/hans-public/api/",
    "USGS CAP Alert": "https://volcanoes.usgs.gov/hans-public/api/",
    "USGS Monitored Volcano": "https://volcanoes.usgs.gov/hans-public/api/",
    "USGS Notice": "https://volcanoes.usgs.gov/hans-public/api/",
    "USGS VONA": "https://volcanoes.usgs.gov/hans-public/api/",
    "USGS GeoJSON Volcano": "https://volcanoes.usgs.gov/hans-public/api/",
    "NOAA Alert": "https://www.weather.gov/documentation/services-web-api",
    "NOAA Station": "https://www.weather.gov/documentation/services-web-api",
    "NOAA Radar": "https://www.weather.gov/documentation/services-web-api",
    "NOAA Tides": "https://api.tidesandcurrents.noaa.gov/api/prod/",
    "EPA Water System": "https://www.epa.gov/enviro/envirofacts-data-service-api-v1",
    "NASA Earthdata": "https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal",
    "OpenFEMA": "https://www.fema.gov/about/openfema/api",
    "HIFLD": "https://hifld-geoplatform.opendata.arcgis.com/",
    "MapServer": "https://gis.fema.gov/arcgis/rest/services/",
    "FeatureServer": "https://gis.fema.gov/arcgis/rest/services/"
}

FEMA_ENDPOINTS = [
    "https://gis.fema.gov/arcgis/rest/services/FEMA",
    "https://hazards.fema.gov/arcgis/rest/services",
    "https://hazards.fema.gov/arcgis/rest/services/public/NFHL"
]

OPENFEMA_API = "https://www.fema.gov/api/open/v1/DataSets"
