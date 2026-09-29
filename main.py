from PIL import Image
from PIL.ExifTags import GPSTAGS
from pillow_heif import register_heif_opener
from geopy.geocoders import Nominatim

register_heif_opener()


def convert_to_degrees(value):
    """
    Mengubah GPS EXIF dari DMS:
    (degrees, minutes, seconds)
    menjadi decimal degree.
    """

    degrees = float(value[0])
    minutes = float(value[1])
    seconds = float(value[2])

    return degrees + (minutes / 60) + (seconds / 3600)


# ==============================
# BACA FOTO
# ==============================

image = Image.open("IMG_4987.heic")

exif = image.getexif()

# 0x8825 = GPSInfo
gps_info = exif.get_ifd(0x8825)

gps = {}

for key, value in gps_info.items():
    gps[GPSTAGS.get(key, key)] = value


# ==============================
# CEK GPS
# ==============================

if not gps:
    print("❌ GPS tidak ditemukan di foto.")
    exit()


# ==============================
# AMBIL KOORDINAT
# ==============================

latitude = convert_to_degrees(gps["GPSLatitude"])
longitude = convert_to_degrees(gps["GPSLongitude"])


# ==============================
# SESUAIKAN ARAH
# ==============================

if gps["GPSLatitudeRef"] == "S":
    latitude = -latitude

if gps["GPSLongitudeRef"] == "W":
    longitude = -longitude


# ==============================
# GOOGLE MAPS
# ==============================

google_maps_url = (
    f"https://www.google.com/maps?q={latitude},{longitude}"
)


# ==============================
# REVERSE GEOCODING
# ==============================

geolocator = Nominatim(
    user_agent="cekpoto-osint"
)

location = geolocator.reverse(
    f"{latitude}, {longitude}",
    language="id"
)


# ==============================
# HASIL ALAMAT
# ==============================

address = {}

if location:
    address = location.raw.get("address", {})


# ==============================
# AMBIL DETAIL WILAYAH
# ==============================

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


# ==============================
# KHUSUS JAKARTA
# ==============================

if "Jakarta" in (location.address if location else ""):

    if not provinsi:
        provinsi = "Daerah Khusus Ibukota Jakarta"

    # Jika city belum mendapatkan Jakarta Selatan,
    # coba ambil dari county
    if not kabupaten_kota:
        kabupaten_kota = (
            address.get("county")
            or address.get("city")
        )


# ==============================
# OUTPUT
# ==============================

print("\n==============================")
print("       📍 FOTO LOCATION")
print("==============================")

print(f"Latitude       : {latitude}")
print(f"Longitude      : {longitude}")

print("\n🏠 ALAMAT")

if location:
    print(location.address)
else:
    print("Alamat tidak ditemukan.")


print("\n🏙️ WILAYAH")

print(f"Desa/Kelurahan : {desa or '-'}")
print(f"Kecamatan      : {kecamatan or '-'}")
print(f"Kabupaten/Kota : {kabupaten_kota or '-'}")
print(f"Provinsi       : {provinsi or '-'}")
print(f"Negara         : {negara or '-'}")


print("\n🌎 GOOGLE MAPS")

print(google_maps_url)

print("==============================")