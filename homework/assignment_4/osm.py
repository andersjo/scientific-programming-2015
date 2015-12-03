# coding:utf-8
import logging
from xml import sax
from math import radians, cos, sin, asin, sqrt
import networkx as nx


class NodePoint(object):
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def dist(self, other):
        return gc_dist(self.lat, self.lon, other.lat, other.lon)

class Way(object):
    def __init__(self, id):
        self.id = id
        self.node_ids = []
        self.tags = {}
        self.accessibility = None

    def update_accessibility(self):
        self.accessibility = WayAccessibility(self.tags)


class WayMap(object):
    def __init__(self):
        self.nodes = {}
        self.ways = {}

    def to_networkx(self):
        G = nx.DiGraph()
        for way in self.ways.values():
            if not (way.accessibility.direct_accessible() or way.accessibility.reverse_accessible()):
                continue

            for n1_id, n2_id in zip(way.node_ids, way.node_ids[1:]):
                n1 = self.nodes[n1_id]
                n2 = self.nodes[n2_id]
                node_dist = n1.dist(n2)

                # Nodes
                for n_id in (n1_id, n2_id):
                    if n_id not in G.node:
                        G.add_node(n_id,
                                   lat=self.nodes[n_id].lat,
                                   lon=self.nodes[n_id].lon)

                # Edges
                if way.accessibility.direct_accessible():
                    G.add_edge(n1_id, n2_id,
                               way=way,
                               dist=node_dist,
                               car=way.accessibility.car_direct,
                               bike=way.accessibility.bike_direct,
                               foot=way.accessibility.foot)
                if way.accessibility.reverse_accessible():
                    G.add_edge(n2_id, n1_id,
                               way=way,
                               dist=node_dist,
                               car=way.accessibility.car_reverse,
                               bike=way.accessibility.bike_reverse,
                               foot=way.accessibility.foot)

        return G

    def streets(self):
        street_names = {}
        for way in self.ways.values():
            if 'highway' in way.tags and 'name' in way.tags:
                street_names[way.tags['name']] = way
        return street_names

class WayParserHandler(sax.handler.ContentHandler):
    def __init__(self):
        self.data = WayMap()
        self.in_elem = ""
        self.current_way = None

    def startElement(self, name, attrs):
        if name == "node":
            self.data.nodes[int(attrs['id'])] = NodePoint(float(attrs['lat']), float(attrs['lon']))
        elif name == "way":
            self.current_way = Way(int(attrs['id']))
            self.in_elem = "way"

        elif self.in_elem == "way":
            if name == "nd":
                self.current_way.node_ids.append(int(attrs['ref']))
            elif name == "tag":
                self.current_way.tags[attrs['k']] = attrs['v']

        # self.in_elem = name

    def endElement(self, name):
        if name == 'way' and self.current_way:
            self.current_way.update_accessibility()
            self.data.ways[self.current_way.id] = self.current_way
            self.current_way = None
            self.in_elem = None


def gc_dist(lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees).

        The distance is returned in meters.
        """
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # http://en.wikipedia.org/wiki/Haversine_formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))

        RADIUS_OF_EARTH_IN_KM = 6367
        km = RADIUS_OF_EARTH_IN_KM * c
        return km * 1000


class WayAccessibility(object):
    """The code here is adapted from osm4routing

    https://github.com/Tristramg/osm4routing
    """
    def __init__(self, attrs):
        self.bike_direct = None
        self.foot = None
        self.car_direct = None
        self.bike_reverse = None
        self.car_reverse = None
        
        for key, val in attrs.items():
            self.update_accessibility(key, val)
        
        self.update_unknowns()
            
    def direct_accessible(self, transport='any'):
        if transport == 'car':
            return self.car_direct != 'car_forbidden'
        elif transport == 'bike':
            return self.bike_direct != 'bike_forbidden'
        elif transport == 'foot':
            return self.foot != 'foot_forbidden'
        else:
            return (self.car_direct != 'car_forbidden') or (self.bike_direct != 'bike_forbidden') \
                   or (self.foot != 'foot_forbidden') 
    
    def reverse_accessible(self, transport='any'):
        if transport == 'car':
            return self.car_reverse != 'car_forbidden'
        elif transport == 'bike':
            return self.bike_reverse != 'bike_forbidden'
        elif transport == 'foot':
            return self.foot != 'foot_forbidden'
        else:
            return (self.car_reverse != 'car_forbidden') or (self.bike_reverse != 'bike_forbidden') \
                   or (self.foot != 'foot_forbidden')


    def update_unknowns(self):
        if not self.car_reverse and self.car_direct:
            self.car_reverse = self.car_direct
        if not self.bike_reverse and self.bike_direct:
            self.bike_reverse = self.bike_reverse
        if not self.car_direct:
            self.car_direct = 'car_forbidden'
        if not self.bike_direct:
            self.bike_direct = 'bike_forbidden'
        if not self.car_reverse:
            self.car_reverse = 'car_forbidden'
        if not self.bike_reverse:
            self.bike_reverse = 'bike_forbidden'
        if not self.foot:
            self.foot = 'foot_forbidden'
            
    def update_accessibility(self, key, val):
        if key == 'highway':
            if val in ("cycleway", "path", "footway", "steps", "pedestrian"):
                self.bike_direct = 'bike_track'
                self.foot = 'foot_allowed'
            elif val in ('primary', 'primary_link'):
                self.car_direct = 'car_primary'
                self.foot = 'foot_allowed'
                self.bike_direct = 'bike_allowed'
            elif val == "secondary":
                self.car_direct = 'car_secondary'
                self.foot = 'foot_allowed'
                self.bike_direct = 'bike_allowed'
            elif val == "tertiary":
                self.car_direct = 'car_tertiary'
                self.foot = 'foot_allowed'
                self.bike_direct = 'bike_allowed'
            elif val in ("unclassified", "residential", "living_street", "road", "service", "track"):
                self.car_direct = 'car_residential'
                self.foot = 'foot_allowed'
                self.bike_direct = 'bike_allowed'
            elif val in ("motorway", "motorway_link"):
                self.car_direct = 'car_motorway'
                self.foot = 'foot_forbidden'
                self.bike_direct = 'bike_forbidden'
            elif val in ("trunk", "trunk_link"):
                self.car_direct = 'car_trunk'
                self.foot = 'foot_forbidden'
                self.bike_direct = 'bike_forbidden'
    
        elif key == "pedestrian" or  key == "foot":
            if val in ("yes", "designated", "permissive"):
                self.foot = 'foot_allowed'
            elif val == "no":
                self.foot = 'foot_forbidden'
            else:
                logging.info("Unhandled key-value pair {}={} ".format(key, val))
    
        # http://wiki.openstreetmap.org/wiki/Cycleway
        ##// http://wiki.openstreetmap.org/wiki/Map_Features#Cycleway
        elif key == "cycleway":
            if val in ("lane", "yes", "true", "lane_in_the_middle"):
                self.bike_direct = 'bike_lane'
            elif val == "track":
                self.bike_direct = 'bike_track'
            elif val == "opposite_lane":
                self.bike_reverse = 'bike_lane'
            elif val == "opposite_track":
                self.bike_reverse = 'bike_track'
            elif val == "opposite":
                self.bike_reverse = 'bike_allowed'
            elif val == "share_busway":
                self.bike_direct = 'bike_busway'
            elif val == "lane_left":
                self.bike_reverse = 'bike_lane'
            else:
                self.bike_direct = 'bike_lane'
        
        elif key == "bicycle":
        
            if val in ("yes" , "permissive" , "destination" , "designated" , "private" , "true"):
                self.bike_direct = 'bike_allowed'
            elif val in ("no", "true"):
                self.bike_direct = 'bike_forbidden'
            else:
                logging.info("Unhandled key-value pair {}={} ".format(key, val))
    
    
        elif key == "busway":
            if val in ("yes" , "track" , "lane"):
                self.bike_direct = 'bike_busway'
            elif val in ("opposite_lane", "opposite_track"):
                self.bike_reverse = 'bike_busway'
            else:
                self.bike_direct = 'bike_busway'
        
        elif key == "oneway":
            if val in ("yes", "true", "1"):
                self.car_reverse = 'car_forbidden'
                if self.bike_reverse is None:
                    self.bike_reverse = 'bike_forbidden'
            
        elif key == "junction":
            if val == "roundabout":
                self.car_reverse = 'car_forbidden'
                if self.bike_reverse is None:
                    self.bike_reverse = 'bike_forbidden'
            

def read_way_network(filename):
    handler = WayParserHandler()
    sax.parse(filename, handler)
    return handler.data.to_networkx()

# print ways
# for id, way in ways.ways.items()[0:10]:
#     print way.node_ids
#     print way.tags
#     print "direct accessible", way.accessibility.direct_accessible()
#     print "reverse accessible", way.accessibility.reverse_accessible()

# G = to_networkx(ways)
# street_names = ways.streets()
# # Find from
# from_name = u'Hollænderdybet'
# to_name = u'Bergthorasgade'
#
# from_node_id = street_names[from_name].node_ids[0]
# to_node_id = street_names[to_name].node_ids[0]
#
# print u"Finding shortest path from {} ({}) to {} ({})".format(from_name, from_node_id, to_name, to_node_id)
# print nx.shortest_path(G, from_node_id, to_node_id, 'dist')





# # #print handler.notecount
# # #return handler.ergebnis
# #
