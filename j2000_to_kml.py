import csv
from astropy import units as u
from astropy.coordinates import GCRS, ITRS, CartesianRepresentation
from astropy.time import Time
from lxml import etree
from pykml.factory import KML_ElementMaker as KML

# Define the event name (example)
event_name = "drag_s2s3_separation"

def convert_j2000_to_geographic(x, y, z, event_time):
    # Convert the time to an ISO format string
    iso_time = convert_seconds_to_iso(event_time)
    cartesian = CartesianRepresentation(x * u.km, y * u.km, z * u.km)

    # Create a GCRS coordinate object
    gcrs = GCRS(cartesian, obstime=Time(iso_time)) #   A coordinate or frame in the Geocentric Celestial Reference System (GCRS). GCRS is distinct form ICRS mainly in that it is relative to the Earth's center-of-mass rather than the solar system Barycenter.

    # Transform to ITRS (Inertial Terrestrial Reference System)
    itrs = gcrs.transform_to(ITRS(obstime=Time(iso_time))) # A coordinate or frame in the International Terrestrial Reference System (ITRS). Topocentric ITRS frames are convenient for observations of near Earth objects where stellar aberration is not included.

    # Extract latitude, longitude, and altitude
    lat = itrs.spherical.lat.degree
    lon = itrs.spherical.lon.degree
    alt = itrs.spherical.distance.to(u.km).value

    # Debugging information to check values
    print(f"J2000 Coordinates: x={x}, y={y}, z={z}, Time={event_time}")
    print(f"Converted Geographic Coordinates: lat={lat}, lon={lon}, alt={alt}")

    return lat, lon, alt

def convert_seconds_to_iso(seconds):
    # The epoch is set to some known reference time, e.g., J2000
    j2000_epoch = Time("2000-01-01T00:00:00", scale='utc')  # J2000 epoch should be at 12, but it is wrong
    return (j2000_epoch + seconds * u.s).iso

def save_kml_output(latitudes, longitudes, altitudes, event_name):
    # Create KML document structure
    kml_doc = KML.kml(
        KML.Document(
            KML.name(f"Trajectory {event_name}"),
            KML.Placemark(
                KML.name(f"Trajectory {event_name}"),
                KML.LineString(
                    KML.coordinates(
                        " ".join(f"{lon},{lat},{alt}" for lon, lat, alt in zip(longitudes, latitudes, altitudes))
                    )
                )
            )
        )
    )

    # Save to KML file
    with open(f"kml_trajectory_{event_name}.kml", "wb") as kml_file:
        kml_file.write(etree.tostring(kml_doc, pretty_print=True))

def propagate_and_convert(csv_filename, event_name):
    latitudes = []
    longitudes = []
    altitudes = []

    with open(csv_filename, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)  # Skip the header

        for row in csv_reader:
            time = float(row[0])  # Time in seconds
            x = float(row[1])      # X position in km
            y = float(row[2])      # Y position in km
            z = float(row[3])      # Z position in km
            
            lat, lon, alt = convert_j2000_to_geographic(x, y, z, time)
            
            # # Optional: Adjust longitude wrapping
            # lon = (lon + 180) % 360 - 180
            
            # hard fix to move starting point to launch pad
            # launch long and lat with 00tt reference epoch: -1.5486284922357072,60.67360076667758
            # actual launch pad coords 60deg 49' 07'' (N), 0deg 46'27'' (W), converted to 60.81861111111111, -0.7741666666666667
            # hard fix
            lon += (-0.7741666666666667 - 358.49315222750636) # difference real wrt computed
            lat += (60.81861111111111 - 60.67360084382402) # difference real wrt computed

            latitudes.append(lat)
            longitudes.append(lon)
            altitudes.append(alt)

    save_kml_output(latitudes, longitudes, altitudes, event_name)

# Example usage
csv_filename = f"propagated_state_vector_{event_name}.csv"  # Make sure this file exists
propagate_and_convert(csv_filename, event_name)
