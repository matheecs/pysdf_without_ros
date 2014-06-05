from __future__ import print_function

import itertools
import os
import xml.etree.ElementTree as ET
import xml.dom.minidom
import numbers

from tf.transformations import *


def prettyXML(uglyXML):
  return xml.dom.minidom.parseString(uglyXML).toprettyxml(indent='  ')


def homogeneous2translation_quaternion(homogeneous):
  """
  Translation: [x, y, z]
  Quaternion: [x, y, z, w]
  """
  translation = translation_from_matrix(homogeneous)
  quaternion = quaternion_from_matrix(homogeneous)
  return translation, quaternion


def rounded(val):
  if isinstance(val, numbers.Number):
    return int(round(val,6) * 1e5) / 1.0e5
  else:
    return numpy.array([rounded(v) for v in val])


def homogeneous2tq_string(homogeneous):
  return 't=%s q=%s' % homogeneous2translation_quaternion(homogeneous)


def homogeneous2tq_string_rounded(homogeneous):
  return 't=%s q=%s' % tuple(rounded(o) for o in homogeneous2translation_quaternion(homogeneous))


def get_tag(node, tagname, default = None):
  tag = node.findall(tagname)
  if tag:
    return tag[0].text
  else:
    return default

def get_node(node, tagname, default = None):
  tag = node.findall(tagname)
  if tag:
    return tag[0]
  else:
    return default


def string2float_list(s):
  return [float(i) for i in s.split()]


def pose_string2homogeneous(pose):
  pose_float = string2float_list(pose)
  translate = pose_float[:3]
  angles = pose_float[3:]
  homogeneous = compose_matrix(None, None, angles, translate)
  return homogeneous


def get_tag_pose(node):
  pose = get_tag(node, 'pose', '0 0 0  0 0 0')
  return pose_string2homogeneous(pose)


def indent(string, spaces):
  return string.replace('\n', '\n' + ' ' * spaces).strip()






class SDF(object):
  def __init__(self, **kwargs):
    self.world = World()
    if 'file' in kwargs:
      self.from_file(kwargs['file'])


  def from_file(self, filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    if root.tag != 'sdf':
      print('Not a SDF file. Aborting.')
      return
    self.version = float(root.attrib['version'])
    self.world.from_tree(root)



class World(object):
  def __init__(self):
    self.name = '__default__'
    self.models = []
    self.lights = []


  def from_tree(self, node):
    if node.findall('world'):
      node = node.findall('world')[0]
      # TODO lights
    self.models = [Model(tree=model_node) for model_node in node.findall('model')]




class SpatialEntity(object):
  def __init__(self):
    self.name = ''
    self.pose = identity_matrix()


  def __repr__(self):
    return ''.join((
      'name: %s\n' % self.name,
      'pose: %s\n' % homogeneous2tq_string_rounded(self.pose),
    ))


  def from_tree(self, node):
    if node == None:
      return
    self.name = node.attrib['name']
    self.pose = get_tag_pose(node)



class Model(SpatialEntity):
  def __init__(self, **kwargs):
    super(Model, self).__init__()
    self.submodels = []
    self.links = []
    self.joints = []
    if 'tree' in kwargs:
      self.from_tree(kwargs['tree'])


  def __repr__(self):
    return ''.join((
      'Model(\n', 
      '  %s\n' % indent(super(Model, self).__repr__(), 2),
      '  links:\n',
      '    %s' % '\n    '.join([indent(str(l), 4) for l in self.links]),
      '\n',
      '  joints:\n',
      '    %s' % '\n    '.join([indent(str(j), 4) for j in self.joints]),
      '\n',
      ')'
    ))


  def from_tree(self, node):
    if node == None:
      return
    if node.tag != 'model':
      print('Invalid node of type %s instead of model. Aborting.' % node.tag)
      return
    super(Model, self).from_tree(node)
    self.links = [Link(self, tree=link_node) for link_node in node.iter('link')]
    self.joints = [Joint(self, tree=joint_node) for joint_node in node.iter('joint')]



  def to_urdf(self):
    # TODO
    return ''


  def save_urdf(self, filename):
    urdf_file = open(filename, 'w')
    pretty_urdf_string = prettyXML(self.to_urdf())
    urdf_file.write(pretty_urdf_string)
    urdf_file.close()



class Link(SpatialEntity):
  def __init__(self, parent_model, **kwargs):
    super(Link, self).__init__()
    self.parent_model = parent_model
    self.gravity = True
    self.inertial = Inertial()
    self.collision = Collision()
    self.visual = Visual()
    if 'tree' in kwargs:
      self.from_tree(kwargs['tree'])


  def __repr__(self):
    return ''.join((
      'Link(\n',
      '  %s\n' % indent(super(Link, self).__repr__(), 2),
      '  %s\n' % indent(str(self.inertial), 2),
      '  collision: %s\n' % self.collision,
      '  visual: %s\n' % self.visual,
      ')'
    ))


  def from_tree(self, node):
    if node == None:
      return
    if node.tag != 'link':
      print('Invalid node of type %s instead of link. Aborting.' % node.tag)
      return
    super(Link, self).from_tree(node)
    self.inertial = Inertial(tree=get_node(node, 'inertial'))
    self.collision = Collision(tree=get_node(node, 'collision'))
    self.visual = Visual(tree=get_node(node, 'visual'))



class Joint(SpatialEntity):
  def __init__(self, parent_model, **kwargs):
    super(Joint, self).__init__()
    self.parent_model = parent_model
    self.parent = ''
    self.child = ''
    self.axis = Axis()
    if 'tree' in kwargs:
      self.from_tree(kwargs['tree'])


  def __repr__(self):
    return ''.join((
      'Joint(\n',
      '  %s\n' % indent(super(Joint, self).__repr__(), 2),
      '  parent: %s\n' % self.parent,
      '  child: %s\n' % self.child,
      ')'
    ))


  def from_tree(self, node):
    if node.tag != 'joint':
      print('Invalid node of type %s instead of joint. Aborting.' % node.tag)
      return
    super(Joint, self).from_tree(node)
    #TODO self.pose = numpy.dot(self.child.pose, self.pose)
    # TODO



class Axis(object):
  def __init__(self):
    self.xyz = numpy.array([0, 0, 0])



class Inertial(object):
  def __init__(self, **kwargs):
    self.pose = identity_matrix()
    self.mass = 0
    self.inertia = Inertia()
    if 'tree' in kwargs:
      self.from_tree(kwargs['tree'])


  def __repr__(self):
    return ''.join((
      'Inertial(\n',
      '  pose: %s\n' % homogeneous2tq_string_rounded(self.pose),
      '  mass: %s\n' % self.mass,
      '  inertia: %s\n' % self.inertia,
      ')'
    ))


  def from_tree(self, node):
    if node == None:
      return
    if node.tag != 'inertial':
      print('Invalid node of type %s instead of inertial. Aborting.' % node.tag)
      return
    self.pose = get_tag(node, 'pose', identity_matrix())
    self.mass = get_tag(node, 'mass', 0)
    self.inertia = Inertia(tree=get_tag(node, 'inertia'))


class Inertia(object):
  def __init__(self, **kwargs):
    self.ixx = 0
    self.ixy = 0
    self.ixz = 0
    self.iyy = 0
    self.iyz = 0
    self.izz = 0
    if 'tree' in kwargs:
      self.from_tree(kwargs['tree'])


  def __repr__(self):
    return 'Inertia(ixx=%s, ixy=%s, ixz=%s, iyy=%s, iyz=%s, izz=%s)' % (self.ixx, self.ixy, self.ixz, self.iyy, self.iyz, self.izz)


  def from_tree(self, node):
    if node == None:
      return
    if node.tag != 'inertia':
      print('Invalid node of type %s instead of inertia. Aborting.' % node.tag)
      return
    for coord in 'ixx', 'ixy', 'ixz', 'iyy', 'iyz', 'izz':
      self[coord] = get_tag(node, coord, 0)



class LinkPart(SpatialEntity):
  def __init__(self, **kwargs):
    super(LinkPart, self).__init__()
    self.geometry_type = None
    self.geometry_data = {}
    if 'tree' in kwargs:
      self.from_tree(kwargs['tree'])


  def from_tree(self, node):
    if node == None:
      return
    if node.tag != 'visual' and node.tag != 'collision':
      print('Invalid node of type %s instead of visual or collision. Aborting.' % node.tag)
      return
    super(LinkPart, self).from_tree(node)
    gnode = get_node(node, 'geometry')
    if gnode == None:
      return
    for gtype in 'box', 'cylinder', 'sphere', 'mesh':
      typenode = get_node(gnode, gtype)
      if typenode != None:
        self.geometry_type = gtype
        if gtype == 'box':
          self.geometry_data = {'size': get_tag(typenode, 'size')}
        elif gtype == 'cylinder':
          self.geometry_data = {'radius': get_tag(typenode, 'radius'), 'length': get_tag(typenode, 'length')}
        elif gtype == 'sphere':
          self.geometry_data = {'radius': get_tag(typenode, 'radius')}
        elif gtype == 'mesh':
          self.geometry_data = {'uri': get_tag(typenode, 'uri'), 'scale': get_tag(typenode, 'scale')}


  def __repr__(self):
    return 'geometry_type: %s, geometry_data: %s' % (self.geometry_type, self.geometry_data)



class Collision(LinkPart):
  def __init__(self, **kwargs):
    super(Collision, self).__init__(**kwargs)


  def __repr__(self):
    return 'Collision(%s)' % super(Collision, self).__repr__()



class Visual(LinkPart):
  def __init__(self, **kwargs):
    super(Visual, self).__init__(**kwargs)


  def __repr__(self):
    return 'Visual(%s)' % super(Visual, self).__repr__()