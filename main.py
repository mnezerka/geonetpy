#!/usr/bin/env python
import sys
import logging
import string
from functools import update_wrapper
from geonetpy import match, interpolation, geojson
import gpxpy.gpx
import click

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

@click.group()
def root():
    pass

@root.group(chain=True)
@click.pass_context
def track(ctx):
    """This script processes a bunch of gpx tracks through geonet in a unix
    pipe.  One commands feeds into the next.

    Example:

    \b
        track open -i track.gpx interpolate --max-distance 5 html 
    """

    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)

    ctx.obj['points'] = []


@track.command("open")
@click.argument('file', type=click.Path())
@click.pass_context
def open_cmd(ctx, file):
    """Loads one gpx track for processing."""
    
    click.echo(f"Opening '{file}'")
    with open(file, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        points = match.points_from_gpx(gpx)
    ctx.obj['points'] = points

@track.command('interpolate')
@click.option('--max-distance', default=10, show_default=True, help='Maximal distance (in meters) for points interpolation')
@click.pass_context
def interpolate(ctx, max_distance):
    print('number of points in track:', ctx.obj['points'].shape[0])
    interpolated = interpolation.interpolate_distance(ctx.obj['points'], max_distance)
    print('number of points in track after interpolation:', interpolated.shape[0])
    ctx.obj['points'] = interpolated


@track.command('html')
@click.option('--output', default='track', show_default=True, help='Path to files to be generated, e.g. track.html and track.js')
@click.pass_context
def cmd_html(ctx, output):
    print('number of points in track:', ctx.obj['points'].shape[0])
    print('generating geojson content')
    geojson_content = geojson.points_to_geojson(ctx.obj['points'], True)

    tpl_path='templates/tpl_map.html'
    print(f'generating html content from template {tpl_path}')
    with open(tpl_path, 'r') as tpl_file:
        tpl = string.Template(tpl_file.read())

    html_content = tpl.substitute({
        'title': 'Track',
        'geojson': geojson_content
    })

    html_path = f'{output}.html'
    print(f'writing html to {html_path}')
    with open(html_path, 'w') as html_file:
        html_file.write(html_content)

@root.command()
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
    root()
