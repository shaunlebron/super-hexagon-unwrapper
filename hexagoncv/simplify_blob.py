# We want to simplify a blob with redundant vertices to a simple polygon.
# (This helps us deduce the shape of the center blob in super hexagon)

from heap import Heap
import math

############################################################
# Eliminate vertices with the most neglible angles or areas formed by their
# adjacent vertices.
#
# The method applied to area is Visvalingam's algorithm, which is described
# well by Mike Bostock here:
#     http://bost.ocks.org/mike/simplify/

def vector_len(v):
	x,y = v
	return math.sqrt(x*x + y*y)

def vector_area(v0,v1):
	cross = v0[0]*v1[1] - v0[1]*v1[0]
	return abs(cross)

def vector_angle(v0,v1):
	dot = v0[0]*v1[0] + v0[1]*v1[1]
	den = vector_len(v0) * vector_len(v1)
	return math.acos(dot/den)

class PointNode:
	def __init__(self, point):
		self.point = point
		self.area = None
		self.index = None
		self.next_node = None
		self.prev_node = None
	
	def get_vectors(self):
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
		v_prev, v_next = self.get_vectors()
		if v_prev and v_next:
			self.area = vector_area(v_prev, v_next)
		else:
			self.area = None

	def calc_angle(self):
		v_prev, v_next = self.get_vectors()
		if v_prev and v_next:
			self.angle = vector_angle(v_prev, v_next)
		else:
			self.angle = None
	
	def calc(self, key):
		if key == 'area':
			self.calc_area()
		elif key == 'angle':
			self.calc_angle()
	
	def get(self, key):
		if key == 'area':
			return self.area
		elif key == 'angle':
			return self.angle

def simplify_by(points, is_higher, should_stop, refresh_node):
	length = len(points)

	# build nodes
	nodes = [PointNode(p) for p in points]

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
		node.heap_index = i
	
	heap = Heap(nodes, is_higher, on_index_change)
	
	while True:
		node = heap.peek()
		if should_stop(node):
			break
		heap.pop()
		prev_node, next_node = node.prev_node, node.next_node
		prev_node.next_node = next_node
		next_node.prev_node = prev_node
		refresh_node(prev_node)
		heap.reorder_node(prev_node.heap_index)
		refresh_node(next_node)
		heap.reorder_node(next_node.heap_index)

	return [node.point for node in sorted(heap.array, key=(lambda node: node.orig_index))]

def simplify_by_area(points, epsilon=400):
	return simplify_by(points,
		is_higher    = lambda a,b  : a.area < b.area,
		should_stop  = lambda node : node.area > epsilon,
		refresh_node = lambda node : node.calc_area()) 

def simplify_by_angle(points, epsilon=math.pi*0.8):
	return simplify_by(points,
		is_higher    = lambda a,b  : a.angle > b.angle,
		should_stop  = lambda node : node.angle < epsilon,
		refresh_node = lambda node : node.calc_angle())

