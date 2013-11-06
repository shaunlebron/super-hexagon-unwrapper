"""
Utility for reducing a polygon's vertices by creating a simpler approximation.
"""

from heap import Heap
import math

def vector_len(v):
    """Get length of 2D vector."""
    x,y = v
    return math.sqrt(x*x + y*y)

def vector_area(v0,v1):
    """Get area of the triangle created by two 2D vectors."""
    cross = v0[0]*v1[1] - v0[1]*v1[0]
    return abs(cross)/2

def vector_angle(v0,v1):
    """Get angle between two 2D vectors."""
    dot = v0[0]*v1[0] + v0[1]*v1[1]
    den = vector_len(v0) * vector_len(v1)
    return math.acos(dot/den)

class VertexNode:
    """
    This represents a polygon as a doubly-linked list of 2D vertex nodes.
    (i.e. each vertex has a reference to its adjacent vertices)

    Also stores attributes calculated from adjacent vertices:
    * triangle area
    * angle
    """
    
    def __init__(self, point):
        self.point = point
        self.next_node = None
        self.prev_node = None
    
    def get_adj_vectors(self):
        """Get the adjacent vertices relative to this vertex."""
        v_prev = None
        v_next = None
        x0,y0 = self.point
        if self.prev_node:
            x,y = self.prev_node.point
            v_prev = (x-x0,y-y0)
        if self.next_node:
            x,y = self.next_node.point
            v_next = (x-x0,y-y0)
        return v_prev, v_next
    
    def calc_area(self):
        """Calculate the triangle area created by this vertex and its adjacents."""
        v_prev, v_next = self.get_adj_vectors()
        if v_prev and v_next:
            self.area = vector_area(v_prev, v_next)
        else:
            self.area = None

    def calc_angle(self):
        """Calculate the area created by this vertex and its adjacents."""
        v_prev, v_next = self.get_adj_vectors()
        if v_prev and v_next:
            self.angle = vector_angle(v_prev, v_next)
        else:
            self.angle = None
    
def simplify_polygon_by(points, is_higher, should_stop, refresh_node):
    """
    Simplify the given polygon by greedily removing vertices using a given priority.

    This is generalized from Visvalingam's algorithm, which is described well here:
        http://bost.ocks.org/mike/simplify/

    is_higher    = function(a,b) returns node higher in priority to be removed.
    should_stop  = function(a) returns True if given highest priority node stops simplification.
    refresh_node = function(a) refreshes attributes dependent on adjacent vertices.
    """
    length = len(points)

    # build nodes
    nodes = [VertexNode(p) for p in points]

    # connect nodes
    for i in xrange(length):
        prev_i = (i+length-1) % length
        next_i = (i+1) % length
        node = nodes[i]
        node.prev_node = nodes[prev_i]
        node.next_node = nodes[next_i]
        refresh_node(node)
        node.orig_index = i

    def on_index_change(node,i):
        """Callback that allows a node to know its location in the heap."""
        node.heap_index = i
    
    heap = Heap(nodes, is_higher, on_index_change)
    
    while True:
        node = heap.peek()
        if should_stop(node):
            break
        heap.pop()

        # Close gap in doubly-linked list.
        prev_node, next_node = node.prev_node, node.next_node
        prev_node.next_node = next_node
        next_node.prev_node = prev_node

        # Refresh vertices that have new adjacents.
        refresh_node(prev_node)
        heap.reorder_node(prev_node.heap_index)
        refresh_node(next_node)
        heap.reorder_node(next_node.heap_index)

    # Return remaining points in their original order.
    return [node.point for node in sorted(heap.array, key=(lambda node: node.orig_index))]

def simplify_polygon_by_area(points, epsilon=400):
    """
    Simplify polygon by removing vertices whose removal results in the least
    change in area. (Visvalingam's algorithm)
    """
    return simplify_polygon_by(points,
        is_higher    = lambda a,b  : a.area < b.area,
        should_stop  = lambda node : node.area > epsilon,
        refresh_node = lambda node : node.calc_area()) 

def simplify_polygon_by_angle(points, epsilon=math.pi*0.8):
    """
    Simplify polygon by removing vertices that are very close to sitting on a
    straight line between its neighbors.
    """
    return simplify_polygon_by(points,
        is_higher    = lambda a,b  : a.angle > b.angle,
        should_stop  = lambda node : node.angle < epsilon,
        refresh_node = lambda node : node.calc_angle())

