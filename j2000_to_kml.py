"""
This Python script is designed to convert spacecraft trajectory data from Cartesian coordinates in the 
J2000 reference frame to geographic coordinates. It processes state vectors stored in a CSV file, 
transforming them into a KML format for visualization in mapping applications.

Key features include:
- Conversion of Cartesian coordinates to geographic coordinates (latitude, longitude, altitude) using 
astropy's coordinate transformations.
- Generation of KML files that include trajectory paths, impact points, and separation points for 
various events.
- Handling of atmospheric corrections and adjustments for geographical coordinates based on launch pad
locations.

The script uses several libraries, including astropy for astronomical calculations, lxml for 
XML handling, and pykml for KML file generation. 
Functions defined within the script include:
- `convert_j2000_to_geographic`: Transforms J2000 Cartesian coordinates into geographic coordinates.
- `convert_seconds_to_iso`: Converts time from seconds since the J2000 epoch to ISO 8601 format.
- `save_kml_output`: Generates and saves KML output for trajectory visualization.
- `propagate_and_convert`: Reads state vectors from a CSV file, processes them, and invokes KML output generation.

The script is intended for use in launch vehicle simulations, particularly to visualize trajectories and
impact points and areas of spent rocket stages and other components.
"""


import csv
from astropy import units as u
from astropy.coordinates import GCRS, ITRS, CartesianRepresentation
from astropy.time import Time
from lxml import etree
from pykml.factory import KML_ElementMaker as KML
import math
from perturbations import get_impact_radius

# Define the event name (example)
# event_name = 'drag_s1s2_separation'
# event_name = 'drag_s2s3_separation'
# event_name = "drag_s2fairing_separation"

def convert_j2000_to_geographic(x, y, z, event_time):
    """
    Converts Cartesian coordinates in the J2000 reference frame to geographic coordinates (latitude, longitude, altitude).

    Args:
        x (float): The x-coordinate in kilometers.
        y (float): The y-coordinate in kilometers.
        z (float): The z-coordinate in kilometers.
        event_time (float): The event time in seconds since the J2000 epoch.

    Returns:
        tuple: A tuple containing:
            - lat (float): Latitude in degrees.
            - lon (float): Longitude in degrees.
            - alt (float): Altitude in kilometers.
    """
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
    # print(f"J2000 Coordinates: x={x}, y={y}, z={z}, Time={event_time}")
    # print(f"Converted Geographic Coordinates: lat={lat}, lon={lon}, alt={alt}")
    return lat, lon, alt

def convert_seconds_to_iso(seconds):
    """
    Converts a time in seconds since the J2000 epoch to an ISO 8601 formatted string.

    Args:
        seconds (float): The time in seconds since the J2000 epoch.

    Returns:
        str: An ISO 8601 formatted time string corresponding to the input seconds.
    """
    # The epoch is set to some known reference time, e.g., J2000
    j2000_epoch = Time("2000-01-01T00:00:00", scale='utc')  # J2000 epoch should be at 12, but it is wrong
    return (j2000_epoch + seconds * u.s).iso

def save_kml_output(latitudes, longitudes, altitudes, event_name):
    """
    Saves the trajectory and impact information to a KML file for visualization in mapping applications.

    Args:
        latitudes (list of float): List of latitudes in degrees.
        longitudes (list of float): List of longitudes in degrees.
        altitudes (list of float): List of altitudes in kilometers.
        event_name (str): The name of the event associated with the trajectory, used for naming and distinguishing outputs.

    Returns:
        None: The function writes the KML output to a file.
    """
    impact_radius = get_impact_radius(event_name)

    # Create KML document structure
    kml_doc = KML.kml(
        KML.Document(
            KML.name(f"Trajectory {event_name}"),
            
            # Add Separation Point Placemark
            KML.Placemark(
                KML.name(f"Separation Point {event_name}"),
                KML.Point(
                    KML.coordinates(f"{longitudes[0]},{latitudes[0]},{altitudes[0]}")
                ),
                KML.Style(
                    KML.IconStyle(
                        KML.Icon(
                            KML.href("http://maps.google.com/mapfiles/kml/shapes/placemark_square.png")
                        )
                    )
                )
            ),
            
            KML.Placemark(
                KML.name(f"Trajectory {event_name}"),
                KML.LineString(
                    KML.coordinates(
                        " ".join(f"{lon},{lat},{alt}" for lon, lat, alt in zip(longitudes, latitudes, altitudes))
                    )
                )
            ),
            KML.Placemark(
                KML.name(f"Impact Point {event_name}"),
                KML.Point(
                    KML.coordinates(f"{longitudes[-1]},{latitudes[-1]},{altitudes[-1]}")
                ),
                KML.Style(
                    KML.IconStyle(
                        KML.Icon(
                            KML.href("http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png")
                        )
                    )
                )
            ),
            # Add a filled circle around the impact point
            KML.Placemark(
                KML.name("Impact Area"),
                KML.Style(
                    KML.LineStyle(
                        KML.color("ff0000ff"),  # Outline color (red)
                        KML.width(2)
                    ),
                    KML.PolygonStyle(
                        KML.color("7f0000ff"),  # Fill color (semi-transparent red)
                        KML.outline(False)       # Disable outline for polygon
                    )
                ),
                KML.Polygon(
                    KML.outerBoundaryIs(
                        KML.LinearRing(
                            KML.coordinates(
                                " ".join(
                                    f"{longitudes[-1] + (impact_radius / 111.32) * math.cos(math.radians(angle)) / math.cos(math.radians(latitudes[-1]))},{latitudes[-1] + (impact_radius / 111.32) * math.sin(math.radians(angle))},0"
                                    for angle in range(0, 360, 10)  # 36 points to make a circle
                                )
                            )
                        )
                    )
                )
            )
        )
    )

    # Save to KML file
    with open(f"kml_trajectory_{event_name}.kml", "wb") as kml_file:
        kml_file.write(etree.tostring(kml_doc, pretty_print=True))

    # # Save to KML file
    # with open(f"kml_trajectory_{event_name}.kml", "wb") as kml_file:
    #     kml_file.write(etree.tostring(kml_doc, pretty_print=True))

def propagate_and_convert(csv_filename, event_name):
    """
    Propagates the trajectory from a CSV file containing state vectors, converts the coordinates
    from J2000 to geographic coordinates, and saves the results in a KML format.

    Args:
        csv_filename (str): The name of the CSV file containing the state vectors (time, x, y, z).
        event_name (str): The name of the event associated with the trajectory, used for naming outputs.

    Returns:
        None: The function writes the KML output to a file after processing the trajectory data.
    """
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
    print(f'KML file of {event_name} exported')

# # Example usage
# csv_filename = f"propagated_state_vector_{event_name}.csv"  # Make sure this file exists
# propagate_and_convert(csv_filename, event_name)