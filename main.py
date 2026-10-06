from io import BytesIO

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from PIL import Image
from PIL.ExifTags import GPSTAGS
from pillow_heif import register_heif_opener
from geopy.geocoders import Nominatim


# Support HEIC / HEIF
register_heif_opener()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="OSINT Photo API",
    description="API untuk mengambil GPS dan lokasi dari metadata foto",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://5e27-203-142-86-77.ngrok-free.app"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# GPS
# ============================================================

def convert_to_degrees(value):

    degrees = float(value[0])
    minutes = float(value[1])
    seconds = float(value[2])

    return degrees + (minutes / 60) + (seconds / 3600)


def extract_gps(image):

    exif = image.getexif()

    try:
        gps_info = exif.get_ifd(0x8825)
    except Exception:
        return None

    gps = {}

    for key, value in gps_info.items():

        gps[GPSTAGS.get(key, key)] = value

    if not gps:
        return None

    if "GPSLatitude" not in gps:
        return None

    if "GPSLongitude" not in gps:
        return None

    latitude = convert_to_degrees(
        gps["GPSLatitude"]
    )

    longitude = convert_to_degrees(
        gps["GPSLongitude"]
    )

    # Selatan
    if gps.get("GPSLatitudeRef") == "S":
        latitude = -latitude

    # Barat
    if gps.get("GPSLongitudeRef") == "W":
        longitude = -longitude

    return {
        "latitude": latitude,
        "longitude": longitude
    }


# ============================================================
# REVERSE GEOCODING
# ============================================================

def reverse_geocode(latitude, longitude):

    geolocator = Nominatim(
        user_agent="cekpoto-osint-api"
    )

    location = geolocator.reverse(
        f"{latitude}, {longitude}",
        language="id"
    )

    if not location:

        return {
            "address": None,
            "desa_kelurahan": None,
            "kecamatan": None,
            "kabupaten_kota": None,
            "provinsi": None,
            "negara": None
        }

    address = location.raw.get(
        "address",
        {}
    )

    desa = (
        address.get("village")
        or address.get("town")
        or address.get("hamlet")
    )

    kecamatan = (
        address.get("municipality")
        or address.get("suburb")
        or address.get("district")
    )

    kabupaten_kota = (
        address.get("city")
        or address.get("county")
        or address.get("city_district")
    )

    provinsi = (
        address.get("state")
        or address.get("province")
        or address.get("state_district")
    )

    negara = address.get("country")


    # Khusus Jakarta
    if "Jakarta" in location.address:

        if not provinsi:
            provinsi = "Daerah Khusus Ibukota Jakarta"

        if not kabupaten_kota:

            kabupaten_kota = (
                address.get("county")
                or address.get("city")
            )


    return {

        "address": location.address,

        "desa_kelurahan": desa,

        "kecamatan": kecamatan,

        "kabupaten_kota": kabupaten_kota,

        "provinsi": provinsi,

        "negara": negara

    }


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "OSINT Photo API",
        "status": "running"
    }


# ============================================================
# ANALYZE PHOTO
# ============================================================

@app.post("/analyze")
async def analyze_photo(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="File tidak ditemukan"
        )


    # Baca file
    contents = await file.read()


    # Buka gambar
    try:

        image = Image.open(
            BytesIO(contents)
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="File bukan gambar yang valid"
        )


    # Ambil GPS
    gps = extract_gps(image)


    # Kalau tidak ada GPS
    if not gps:

        return {

            "success": True,

            "gps_found": False,

            "message":
                "GPS tidak ditemukan pada metadata foto",

            "filename":
                file.filename

        }


    latitude = gps["latitude"]

    longitude = gps["longitude"]


    # Google Maps
    google_maps_url = (
        f"https://www.google.com/maps"
        f"?q={latitude},{longitude}"
    )


    # Reverse geocoding
    location = reverse_geocode(
        latitude,
        longitude
    )


    return {

        "success": True,

        "gps_found": True,

        "filename":
            file.filename,

        "coordinates": {

            "latitude":
                latitude,

            "longitude":
                longitude

        },

        "location": {

            "address":
                location["address"],

            "desa_kelurahan":
                location["desa_kelurahan"],

            "kecamatan":
                location["kecamatan"],

            "kabupaten_kota":
                location["kabupaten_kota"],

            "provinsi":
                location["provinsi"],

            "negara":
                location["negara"]

        },

        "maps": {

            "google":
                google_maps_url

        }

    }