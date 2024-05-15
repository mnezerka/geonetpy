#!/usr/bin/env python
import sys
import logging
import string
import time
import gpxpy.gpx
import click
import numpy as np
from geonetpy import match, interpolation, geojson
from geonetpy.net import Net
from geonetpy.geojson import tracks_to_geojson

DEFAULT_INTERPOLATION_MAX_DISTANCE = 30

@click.group()
@click.option('--log-level', default='INFO', help='Log level (DEBUG, INFO, ...)')
def root(log_level):
    logging.basicConfig(stream=sys.stderr, level=log_level)

@root.group(chain=True)
def tracks():
    """Track tools and visualization"""

@tracks.command('html')
@click.argument('files', nargs=-1, type=click.Path())
@click.option('--output', default='tracks.html', show_default=True, help='Path to files to be generated, e.g. tracks.html')
@click.option('--max-distance', default=DEFAULT_INTERPOLATION_MAX_DISTANCE, show_default=True, help='Maximal distance (in meters) for points interpolation')
def cmd_tracks_html(files, output, max_distance):

    click.echo(f"rendering to html from {len(files)} files'")

    all_tracks = []
    for filename in files:
        click.echo(f'reading {filename}')
        with open(filename, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            points = match.points_from_gpx(gpx)
            print('number of points in track:', points.shape[0])
            points = interpolation.interpolate_distance(points, max_distance)
            print('number of points in track after interpolation:', points.shape[0])
            all_tracks.append(points)

    geojson_content = geojson.tracks_to_geojson(all_tracks, lines=True)

    tpl_path = 'templates/tpl_map.html'
    print(f'generating html content from template {tpl_path}')
    with open(tpl_path, 'r') as tpl_file:
        tpl = string.Template(tpl_file.read())

    html_content = tpl.substitute({
        'title': 'Tracks',
        'geojson': geojson_content
    })

    print(f'writing html to {output}')
    with open(output, 'w') as html_file:
        html_file.write(html_content)

@tracks.command('match')
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


@root.group()
def net():
    """Geographic net tools"""

@net.command("create")
@click.argument('files', nargs=-1, type=click.Path())
@click.option('--output', default='net', show_default=True, help='File name for generated output (extension is added automaticaly, e.g. net.html)')
@click.option('--output-format', default=['html'], type=click.Choice(['html', 'geojson', 'npz']), show_default=True, multiple=True, help='Output format')
@click.option('--max-distance', default=DEFAULT_INTERPOLATION_MAX_DISTANCE, show_default=True, help='Maximal distance (in meters) for points interpolation')
def net_create_cmd(files, output, output_format, max_distance):
    """Creates network from gpx files"""

    click.echo(f'creating net from {len(files)} files')
    click.echo(f'output format: {output_format}')
    n = Net()
    counter = 1
    for filename in files:
        click.echo(f'adding {filename} {counter}/{len(files)}')
        with open(filename, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            points = match.points_from_gpx(gpx)

            print('number of points in track:', points.shape[0])
            points = interpolation.interpolate_distance(points, max_distance)
            print('number of points in track after interpolation:', points.shape[0])
            print(f'adding {points.shape[0]} points to the net')

            last_spot = None
            start = time.time()
            for point in points:
                last_spot = n.add_point(point, last_spot)

        print(f'stat of the net: {n.stat()}')
        end = time.time()
        duration = end - start
        print(f'duration: {duration}s, per point: {duration/len(points)}s')

        counter += 1

    # print('number of spots in net:', len(n.spots))
    if 'html' in output_format:
        print('generating geojson content')
        geojson_content = n.to_geojson()

        tpl_path = 'templates/tpl_map.html'
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

    if 'geojson' in output_format:
        print('generating geojson content')
        geojson_content = n.to_geojson()

        json_path = f'{output}.json'
        print(f'writing geojson to {json_path}')
        with open(json_path, 'w') as json_file:
            json_file.write(geojson_content)

    if 'npz' in output_format:
        points = np.array(n.get_points())
        edges = np.array(n.get_edges())
        print(f'writing net to {output}.npz (points={len(points)} edges={len(edges)} meta={len(n.meta)})')
        np.savez(output, points=points, edges=edges, meta=n.meta)


@net.command("show")
@click.argument('file', nargs=1, type=click.Path())
@click.option('--output', default='net', show_default=True, help='File name for generated output (extension is added automaticaly, e.g. net.html)')
def net_show_cmd(file, output):
    """Reads and shows geo net loaded from npz file"""

    click.echo(f'loading net from {file}')

    npzfile = np.load(file)
    print(npzfile['meta'])

    n = Net(npzfile['points'], npzfile['edges'])

    print('generating geojson content')
    geojson_content = n.to_geojson()

    tpl_path = 'templates/tpl_map.html'
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
