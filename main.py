#!/usr/bin/env python
import sys
import logging
import string
from functools import update_wrapper
from geonetpy import match, interpolation, geojson
from geonetpy.net import Net
import gpxpy.gpx
import click

DEFAULT_INTERPOLATION_MAX_DISTANCE = 10

@click.group()
@click.option('--log-level', default='INFO', help='Log level (DEBUG, INFO, ...)')
def root(log_level):
    #logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    logging.basicConfig(stream=sys.stderr, level=log_level)

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
    ctx.obj['points'].append(points)

@track.command('interpolate')
@click.option('--max-distance', default=DEFAULT_INTERPOLATION_MAX_DISTANCE, show_default=True, help='Maximal distance (in meters) for points interpolation')
@click.pass_context
def interpolate(ctx, max_distance):
    print('number of points in track:', ctx.obj['points'][0].shape[0])
    interpolated = interpolation.interpolate_distance(ctx.obj['points'][0], max_distance)
    print('number of points in track after interpolation:', interpolated.shape[0])
    ctx.obj['points'][0] = interpolated

@track.command('html')
@click.option('--output', default='track', show_default=True, help='Path to files to be generated, e.g. track.html and track.js')
@click.pass_context
def cmd_html(ctx, output):
    print('number of points in track:', ctx.obj['points'][0].shape[0])
    print('generating geojson content')
    geojson_content = geojson.points_to_geojson(ctx.obj['points'][0], True)

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

@track.command('match')
@click.pass_context
@click.option('--tolerance', default=0.005, show_default=True, help='Tolerance for matching')
def cmd_match(ctx, tolerance):

    if len(ctx.obj['points']) < 2:
           click.echo("Error: Invalid number of tracks in buffer, required at least 2 tracks")
           raise click.Abort()

    t1 = ctx.obj['points'][0]
    t2 = ctx.obj['points'][1]

    print('number of points in tracks:', t1.shape[0], t2.shape[0])

    t1 = interpolation.interpolate_distance(t1, 10)
    t2 = interpolation.interpolate_distance(t2, 10)

    print('number of points in tracks after interpolation:', t1.shape[0], t2.shape[0])

    matches = match.match(t1, t2, tolerance)

    match.get_track_ratios(matches)


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

@root.group()
def net():
    """Geographic net tools"""

@net.command("create")
@click.argument('files', nargs=-1, type=click.Path())
@click.option('--output', default='net', show_default=True, help='Filepath of generated output, e.g. net.html')
@click.option('--output-format', default='-', show_default=True, help='Output format (-, html)')
@click.option('--max-distance', default=DEFAULT_INTERPOLATION_MAX_DISTANCE, show_default=True, help='Maximal distance (in meters) for points interpolation')
def net_create_cmd(files, output, output_format, max_distance):
    """Creates network from gpx files"""

    click.echo(f"Creating net from {len(files)} files'")

    n = Net()
    for filename in files:
        click.echo(f'Adding {filename}')
        with open(filename, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            points = match.points_from_gpx(gpx)

            print('number of points in track:', points.shape[0])
            points = interpolation.interpolate_distance(points, max_distance)
            print('number of points in track after interpolation:', points.shape[0])

            last_hull = None
            for point in points:
                last_hull = n.add_point(point, last_hull)

    print('number of hulls in net:', len(n.hulls))
    if output_format == 'html':
        print('generating geojson content')
        geojson_content = n.to_geojson()

        tpl_path='templates/tpl_map.html'
        print(f'generating html content from template {tpl_path}')
        with open(tpl_path, 'r') as tpl_file:
            tpl = string.Template(tpl_file.read())

        html_content = tpl.substitute({
            'title': 'Net',
            'geojson': geojson_content
        })

        html_path = f'{output}.html'
        print(f'writing html to {html_path}')
        with open(html_path, 'w') as html_file:
            html_file.write(html_content)


if __name__ == '__main__':
    root()
