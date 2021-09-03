import os, sys
import sublime
from unittest import TestCase
from importlib import reload 
currentDir = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(f'{currentDir}/../../YAExpandRegion'))
import yaExpandRegion
reload(yaExpandRegion)

getNextRegion = yaExpandRegion.getNextRegion
fixture = None
fixtureComments = None

class TestFunctions(TestCase):
  @classmethod
  def setUpClass(cls):
    global fixture, fixtureComments
    file = open(f'{currentDir}/fixture.js', 'r')
    fixture = file.read()
    file.close()
    file = open(f'{currentDir}/fixtureComments.js', 'r')
    fixtureComments = file.read()
    file.close()

  def test_1(self):
    """match outer {...} and braket itself"""
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(1,1))
    self.assertEqual(region, sublime.Region(1,176))
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(0,0))
    self.assertEqual(region, sublime.Region(0,177))
  def test_2(self):
    """match {}"""
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(48,48))
    self.assertEqual(region, sublime.Region(47,49))
  def test_3(self):
    """match one char Region { }"""
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(60,60))
    self.assertEqual(region, sublime.Region(60,61))
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(61,61), {
      'cachedRegionsForExpand': regionsForExpand,
    })
    self.assertEqual(region, sublime.Region(60,61))
  def test_4(self):
    """match []"""
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(202,203))
    self.assertEqual(region, sublime.Region(202,212))
  def test_5(self):
    """match ()"""
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(248,248))
    self.assertEqual(region, sublime.Region(248,320))
  def test_6(self):
    """not empty selection"""
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(60,61))
    self.assertEqual(region, sublime.Region(59,62))
  
  def test_7(self):
    """match double quote \"some text\" outer and inner """
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(325,326))
    self.assertEqual(region, sublime.Region(325,337))
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(325,337), {
      'cachedRegionsForExpand': regionsForExpand,
    })
    self.assertEqual(region, sublime.Region(324,338))
  def test_8(self):
    """match non capturing string while selection inside [...]"""
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(349,349))
    self.assertEqual(region, sublime.Region(341,388))
  def test_9(self):
    """match [...] inside capturing string"""
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(410,411))
    self.assertEqual(region, sublime.Region(408,415))
  def test_10(self):
    """match capturing string outer and inner"""
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(403,404))
    self.assertEqual(region, sublime.Region(391,433))
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(391,433), {
      'cachedRegionsForExpand': regionsForExpand,
    })
    self.assertEqual(region, sublime.Region(390,434))

  def test_11(self):
    """ignore chars ('... in comments"""
    region, regionsForExpand = getNextRegion(fixtureComments, sublime.Region(48, 49), {
      'commentsRegions': [sublime.Region(0, 21)]
    })
    self.assertEqual(region, sublime.Region(37, 52))

  def test_21(self):
    """match fullWord"""
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(252, 252))
    self.assertEqual(region, sublime.Region(252, 259))
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(252, 259), {
      'cachedRegionsForExpand': regionsForExpand,
    })
    self.assertEqual(region, sublime.Region(249, 319))
  def test_22(self):
    """match fullWord with digits and $"""
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(1055, 1055))
    self.assertEqual(region, sublime.Region(1053, 1062))

  def test_23(self):
    """ignore escaped char \` """
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(1098, 1098))
    self.assertEqual(region, sublime.Region(1086, 1110))
  def test_24(self):
    """ignore escaped char \' """
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(1134, 1134))
    self.assertEqual(region, sublime.Region(1134, 1136))
  def test_25(self):
    """ignore escaped slash \\ """
    region, regionsForExpand = getNextRegion(fixture, sublime.Region(1142, 1142))
    self.assertEqual(region, sublime.Region(1142, 1144))
