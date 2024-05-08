import sys
import logging
from geonetpy import match, interpolation
import click

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

@click.command()
@click.option('--geojson', is_flag=True, default=False, show_default=True, help='Generate geojson file')
@click.option('--html', is_flag=True, default=False, show_default=True, help='Generate html preview file')
@click.option('--log-level', default='INFO', help='Log level (DEBUG, INFO, ...)')
@click.option('--tolerance', default=0.005, show_default=True, help='Tolerance for matching')
@click.argument('file1')
@click.argument('file2')
def match_tracks(geojson, html, log_level, tolerance, file1, file2):

    t1 = match.points_from_gpx_file(file1)
    t2 = match.points_from_gpx_file(file2)

    print('number of points in tracks:', t1.shape[0], t2.shape[0])

    t1 = interpolation.interpolate_distance(t1, 10)
    t2 = interpolation.interpolate_distance(t2, 10)

    print('number of points in tracks after interpolation:', t1.shape[0], t2.shape[0])

    matches = match.match(t1, t2, tolerance)

    geojson = match.matches_to_geojson(matches)

    if html:
        print('generating html')
        with open('matches.js', 'w') as json_file:
            json_file.write('const matches=')
            json_file.write(geojson)

    if geojson:
        print('generating geojson')
        with open('matches.json', 'w') as json_file:
            json_file.write(geojson) 

    match.get_track_ratios(matches)

if __name__ == '__main__':
    match_tracks()
