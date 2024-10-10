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
from astropy.coordinates import GCRS, ITRS, CartesianRepresentation, EarthLocation
from astropy.time import Time
from lxml import etree
from pykml.factory import KML_ElementMaker as KML # libraries for KML exports
# import simplekml # import KML  # to match KML style of other flight safety exports
import math # for impact radius
from perturbations import get_impact_radius
from pyproj import Transformer # for wsg84
from functions_def import convert_j2000_to_geographic

import math

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
    # porcodio_time =  -1 # s in theory to fix the epoch
    return (j2000_epoch + seconds * u.s).iso

def save_kml_output(latitudes, longitudes, altitudes, event_name):
    """
    Saves the trajectory and impact information to a KML file for visualization in mapping applications.
    """
    # Earth's radius in kilometers (mean value)
    # earth_radius_km = 6361.89959939 # this is a hotfix so that the earth radius matches the starting altitude (which should be around 21m SL, but in most simulations is around 30m SL)

    altitudes_relative_to_ground = []  # To store the calculated relative altitudes
    for (alt, latitude) in zip(altitudes, latitudes):
        # earth_radius_m = earth_radius_at_latitude(latitude)*1000 # in km to m
        # altitude_ground = (alt - earth_radius_m)
        # altitudes_relative_to_ground.append(altitude_ground) # in m
        
        altitudes_relative_to_ground.append(alt) # in m

    # Skip getting the impact radius if the event is 'full_trajectory'
    if event_name != 'full_trajectory':
        impact_radius = get_impact_radius(event_name)

    # Create KML document structure
    kml_doc = KML.kml(
        KML.Document(
            KML.name(f"Trajectory {event_name}"),
            
            # Create Style for LineString
            KML.Style(
                KML.LineStyle(
                    KML.color("ff0000ff"),  # Line color (red) / yellow is
                    KML.width(5)             # Line width
                ),
                id="19050"  # Style ID
            ),
            
            # Add Separation Point Placemark
            KML.Placemark(
                KML.name(f"Separation Point {event_name}"),
                KML.Point(
                    KML.altitudeMode("relativeToGround"),  # Set altitude mode
                    KML.coordinates(f"{longitudes[0]},{latitudes[0]},{altitudes_relative_to_ground[0]}")
                ),
                KML.Style(
                    KML.IconStyle(
                        KML.Icon(
                            KML.href("http://maps.google.com/mapfiles/kml/shapes/placemark_square.png")
                        )
                    )
                )
            ),
            
            # Trajectory LineString Placemark
            KML.Placemark(
                KML.name(f"Trajectory {event_name}"),
                KML.LineString(
                    KML.extrude(1),  # Enable extrusion
                    KML.altitudeMode("relativeToGround"),  # Set altitude mode
                    KML.coordinates(
                        " ".join(f"{lon},{lat},{alt}" for lon, lat, alt in zip(longitudes, latitudes, altitudes_relative_to_ground))
                    )
                ),
                KML.styleUrl("#19050")  # Link to the LineStyle defined above
            ),
            
            # Add Impact Point Placemark
            KML.Placemark(
                KML.name(f"Impact Point {event_name}"),
                KML.Point(
                    KML.altitudeMode("relativeToGround"),  # Set altitude mode
                    KML.coordinates(f"{longitudes[-1]},{latitudes[-1]},{altitudes_relative_to_ground[-1]}")
                ),
                KML.Style(
                    KML.IconStyle(
                        KML.Icon(
                            KML.href("http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png")
                        )
                    )
                )
            ),
            # Add a filled circle around the impact point if the event is not 'full_trajectory'
            *(
                [
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
                ] if event_name != 'full_trajectory' else []
            )
        )
    )

    # Save to KML file
    with open(f"kml_trajectory_{event_name}.kml", "wb") as kml_file:
        kml_file.write(etree.tostring(kml_doc, pretty_print=True, xml_declaration=True, encoding='UTF-8'))

    # Save to KML file
    with open(f"kml_trajectory_{event_name}.kml", "wb") as kml_file:
        kml_file.write(etree.tostring(kml_doc, pretty_print=True))

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
            # lat, lon, alt = convert_j2000_to_wgs84(x, y, z, time)
            # lat, lon, alt = convert_eci_to_geodetic(x, y, z, time)
           
            # hard fix to move starting point to launch pad
            # launch long and lat with 00tt reference epoch: -1.5486284922357072,60.67360076667758
            # actual launch pad coords 60deg 49' 07'' (N), 0deg 46'27'' (W), converted to 60.81861111111111, -0.7741666666666667
            # lon += (-0.7741666666666667 - 358.49315222750636) # difference real wrt computed
            # lon += (-0.7741666666666667 - 98.4657879425389) # difference real wrt computed
            # lat += (60.83901472093895 - 60.67360084382402) # difference real wrt computed
            # -1.5068477407153864,60.83764877405799
            latitudes.append(lat)
            longitudes.append(lon)
            altitudes.append(alt)

    save_kml_output(latitudes, longitudes, altitudes, event_name)
    print(f'KML file of {event_name} exported')

# Example usage
#### Exporting KML for trajectories
event_names = ['drag_s1s2_separation', 'drag_s2fairing_separation', 'drag_s2s3_separation', 'full_trajectory']
csv_filenames = []
for event_name in event_names:
    if event_name == 'full_trajectory':
        csv_filename = f"state_vector_{event_name}.csv"
    else:
        csv_filename = f"propagated_state_vector_{event_name}.csv"  # Make sure this file exists
    csv_filenames.append(csv_filename)
for event_name, csv_filename in zip(event_names, csv_filenames):
    propagate_and_convert(csv_filename, event_name)