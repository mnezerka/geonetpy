# geonetpy 

Tools and algorithms for building geographical networks. 


## interpolaton

Load gpx track and render it to html:
```bash
./main.py track open examples/raci_udoli.gpx interpolate html
```
![x](images/raci_udoli_raw.jpg)

Load same gpx track, interpolate points (default max distance is 10m) and render it to html:

```bash
./main.py track open examples/raci_udoli.gpx html
```
![x](images/raci_udoli_interpolated.jpg)

## match submodule

Computes the overlapping segments/clusters of two GPS tracks. It uses KDTree
and clusterization algorithm 

## notes

### gps coordinates

* lat - angle between the equatorial plane and the straight line that passes through that point and through (or close to) the center of the Earth
* lng - angle east or west of a reference meridian to another meridian that passes through that point.

Example:
```
                    lat           lng
cleaveland ohio: 41.4996572N, 81.6936772W 
```
