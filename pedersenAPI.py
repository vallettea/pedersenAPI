import os, sys, json, time
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
from matplotlib.collections import PatchCollection

class Point:
	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z
	def move_y(self, delta):
		self.y += delta
		return self
	def move_z(self, delta):
		self.z += delta
		return self

class Material:
	def __init__(self, rho):
		self.rho = rho

class BBShell:
	def __init__(self, diameter, length, thickness, material):
		self.diameter = diameter
		self.length = length
		self.radius = diameter/2.
		self.thickness = thickness
		self.material = material

	def patch(self):
		return mpatches.Circle((0., 0.), self.radius, fill = False, ec = "k", lw = 2)

	def volume(self):
		surface = np.pi*(self.radius**2 - (self.radius-self.thickness)**2)
		return surface*self.length
	def weight(self):
		return self.volume()*self.material.rho


class Tube:
	def __init__(self, diameter, thickness, material, start, end):
		self.diameter = diameter
		self.start = start
		self.end = end
		self.material = material
		self.thickness = thickness

	def volume(self):
		surface = np.pi*((self.diameter/2.)**2 - (self.diameter/2.-self.thickness)**2)
		length = np.sqrt((self.end.x-self.start.x)**2 + (self.end.y-self.start.y)**2 + (self.end.z-self.start.z)**2)
		return surface*length
	def weight(self):
		return self.volume()*self.material.rho
		
	def patch(self):
		verts = [(self.start.x, self.start.z), (self.end.x, self.end.z)]
		codes = [Path.MOVETO, Path.LINETO]
		path = Path(verts, codes)
		return mpatches.PathPatch(path, lw=2)

class Fork:
	def __init__(self, material, diameter, thickness, alpha4, l5, fork_gap, e3, e4):
		self.material = material
		self.diameter = diameter
		self.thickness = thickness
		self.alpha4 = 180 - alpha4
		self.l5 = l5
		self.components = []
		self.pointA = Point(0, 0, 0)
		self.pointB = Point(0, 0, fork_gap)
		self.e3 = e3
		self.e4 = e4
		self.front_axis = Point(self.l5 * np.sin(np.deg2rad(self.alpha4)) + self.pointA.x, 0, self.l5 * np.cos(np.deg2rad(self.alpha4)) + self.pointA.z )
	
	def assemble(self):
		tube1f = Tube(self.diameter, self.thickness, self.material, self.pointA.move_y(-self.e3/2.), self.pointB)
		tube1b = Tube(self.diameter, self.thickness, self.material, self.pointA.move_y(self.e3/2.), self.pointB)
		beta = np.arctan((self.pointB.x - self.pointA.x)/(self.pointB.z - self.pointA.z))
		self.front_axis = Point(self.l5 * np.sin(np.deg2rad(self.alpha4)+ beta) + self.pointA.x, self.l5 * np.cos(np.deg2rad(self.alpha4) + beta) + self.pointA.z, 0)
		tube2f = Tube(self.diameter, self.thickness, self.material, self.pointA.move_y(-self.e3/2.), self.front_axis.move_y(-self.e4/2.))
		tube2b = Tube(self.diameter, self.thickness, self.material, self.pointA.move_y(self.e3/2.), self.front_axis.move_y(self.e4/2.))
		tube3f = Tube(self.diameter, self.thickness, self.material, self.pointB, self.front_axis.move_y(-self.e4/2.))
		tube3b = Tube(self.diameter, self.thickness, self.material, self.pointB, self.front_axis.move_y(self.e4/2.))
		self.components = [tube1f, tube1b, tube2f, tube2b, tube3f, tube3b]

class Wheel:
	def __init__(self, diameter, center, weight):
		self.diameter = diameter
		self.radius = diameter/2.
		self.center = center
		self.tot_weight = weight
	def patch(self):
		return mpatches.Circle((self.center.x, self.center.z), self.radius, fill = False, ec = "k", lw = 4)
	def weight(self):
		return self.tot_weight

class Frame:
	def __init__(self, material, diameter, thickness, alpha1, alpha2, alpha3, l1, l2, l3, l4, e1, e2, bbshell):
		self.material = material
		self.diameter = diameter
		self.thickness = thickness
		self.alpha1 = alpha1
		self.alpha2 = alpha2
		self.alpha3 = alpha3
		self.e1 = e1
		self.e2 = e2
		self.l1 = l1
		self.l2 = l2
		self.l3 = l3
		self.l4 = l4
		self.bbshell = bbshell
		self.components = [self.bbshell]
		self.fork = None
		self.rear_axis = Point(-self.l4, 0, 0)

	def assemble(self):
		start = Point(self.bbshell.radius * np.cos(np.deg2rad(self.alpha1)), -self.e1/2., self.bbshell.radius * np.sin(np.deg2rad(self.alpha1)) )
		end = Point(self.l1 * np.cos(np.deg2rad(self.alpha1)), 0, self.l1 * np.sin(np.deg2rad(self.alpha1)) )
		tube1f = Tube(self.diameter, self.thickness, self.material, start, end)

		start = Point(self.bbshell.radius * np.cos(np.deg2rad(self.alpha1)), self.e1/2., self.bbshell.radius * np.sin(np.deg2rad(self.alpha1)) )
		end = Point(self.l1 * np.cos(np.deg2rad(self.alpha1)), 0, self.l1 * np.sin(np.deg2rad(self.alpha1)) )
		tube1b = Tube(self.diameter, self.thickness, self.material, start, end)

		start = Point(self.bbshell.radius * np.cos(np.deg2rad(self.alpha2)), -self.e1/2, self.bbshell.radius * np.sin(np.deg2rad(self.alpha2)) )
		end = Point(self.l2 * np.cos(np.deg2rad(self.alpha2)), 0, self.l2 * np.sin(np.deg2rad(self.alpha2)) )
		tube2f = Tube(self.diameter, self.thickness, self.material, start, end)

		start = Point(self.bbshell.radius * np.cos(np.deg2rad(self.alpha2)), self.e1/2, self.bbshell.radius * np.sin(np.deg2rad(self.alpha2)) )
		end = Point(self.l2 * np.cos(np.deg2rad(self.alpha2)), 0, self.l2 * np.sin(np.deg2rad(self.alpha2)) )
		tube2b = Tube(self.diameter, self.thickness, self.material, start, end)

		start = Point(self.bbshell.radius * np.cos(np.deg2rad(self.alpha3)), -self.e1/2, self.bbshell.radius * np.sin(np.deg2rad(self.alpha3)) )
		end = Point(self.l3 * np.cos(np.deg2rad(self.alpha3)), 0, self.l3 * np.sin(np.deg2rad(self.alpha3)) )
		tube3f = Tube(self.diameter, self.thickness, self.material, start, end)

		start = Point(self.bbshell.radius * np.cos(np.deg2rad(self.alpha3)), self.e1/2, self.bbshell.radius * np.sin(np.deg2rad(self.alpha3)) )
		end = Point(self.l3 * np.cos(np.deg2rad(self.alpha3)), 0, self.l3 * np.sin(np.deg2rad(self.alpha3)) )
		tube3b = Tube(self.diameter, self.thickness, self.material, start, end)

		tube4f = Tube(self.diameter, self.thickness, self.material, Point(-self.bbshell.radius, -self.e1/2., 0), Point(-self.l4, -self.e2/2., 0) )
		tube4b = Tube(self.diameter, self.thickness, self.material, Point(-self.bbshell.radius, self.e1/2., 0), Point(-self.l4, self.e2/2., 0) )

		tube5f = Tube(self.diameter, self.thickness, self.material, Point(-self.l4, -self.e2/2., 0), Point(self.l3 * np.cos(np.deg2rad(self.alpha3)), 0, self.l3 * np.sin(np.deg2rad(self.alpha3)) ))
		tube5b = Tube(self.diameter, self.thickness, self.material, Point(-self.l4, self.e2/2., 0), Point(self.l3 * np.cos(np.deg2rad(self.alpha3)), 0, self.l3 * np.sin(np.deg2rad(self.alpha3)) ))

		tube6f = Tube(self.diameter, self.thickness, self.material, Point(-self.l4, -self.e2/2., 0), Point(self.l2 * np.cos(np.deg2rad(self.alpha2)), 0, self.l2 * np.sin(np.deg2rad(self.alpha2)) ))
		tube6b = Tube(self.diameter, self.thickness, self.material, Point(-self.l4, self.e2/2., 0), Point(self.l2 * np.cos(np.deg2rad(self.alpha2)), 0, self.l2 * np.sin(np.deg2rad(self.alpha2)) ))
	
		self.components += [tube1f, tube1b, tube2f, tube2b, tube3f, tube3b, tube4f, tube4b, tube5f, tube5b, tube6f, tube6b]

	def fork_gap(self):
		xs = self.l1 * np.cos(np.deg2rad(self.alpha1))
		ys = self.l1 * np.sin(np.deg2rad(self.alpha1))
		xe = self.l2 * np.cos(np.deg2rad(self.alpha2))
		ye = self.l2 * np.sin(np.deg2rad(self.alpha2))
		return np.sqrt((xe-xs)**2 + (ye-ys)**2)

	def add_fork(self, fork):
		fork.pointA = Point(self.l1 * np.cos(np.deg2rad(self.alpha1)), 0, self.l1 * np.sin(np.deg2rad(self.alpha1)) )
		fork.pointB = Point(self.l2 * np.cos(np.deg2rad(self.alpha2)), 0, self.l2 * np.sin(np.deg2rad(self.alpha2)) )
		fork.assemble()
		self.components += fork.components
		self.fork = fork

	def equate_wheel_axis(self):
		def rotate_y(point, alpha):
			return Point(point.x*np.cos(alpha) - point.z*np.sin(alpha), point.y, point.x*np.sin(alpha) + point.z*np.cos(alpha))
		
		alpha = -np.arctan((self.fork.front_axis.z - self.rear_axis.z)/(self.fork.front_axis.x - self.rear_axis.x))
		for c in self.components:
			if c.__class__.__name__ == "Tube":
				c.start = rotate_y(c.start, alpha)
				c.end = rotate_y(c.end, alpha)
			elif c.__class__.__name__ == "Wheel":
				c.center = rotate_y(c.center, alpha)

	def weight(self):
		return np.sum([x.weight() for x in self.components])


	def plot_schema(self):
		patches = [x.patch() for x in self.components]

		collection = PatchCollection(patches, match_original = True)
		fig = plt.figure(figsize = (9, 9))
		ax = fig.add_subplot(111)
		ax.add_collection(collection)

		plt.axis("equal")
	
		plt.show()

steel = Material(7829e-9)
bbshell = BBShell(68, 100, 2, steel)

frame = Frame(steel, 14, 0.9, 40, 80, 125, 500, 900, 900, 500, 50, 80, bbshell)
frame.assemble()
fork = Fork(steel, 14, 0.9, 20, 400, frame.fork_gap(), 50, 80)

frame.add_fork(fork)


rear_wheel = Wheel(700, frame.rear_axis, 0)
front_wheel = Wheel(700, frame.fork.front_axis, 0)
frame.components += [front_wheel, rear_wheel]
frame.equate_wheel_axis()
frame.plot_schema()

print "weight: %s" % str(frame.weight())