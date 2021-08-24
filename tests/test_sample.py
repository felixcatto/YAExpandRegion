import os, sys
import sublime
from unittest import TestCase
from importlib import reload 
currentDir = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(f'{currentDir}/../../YAExpandRegion'))
# from yaExpandRegion import getNextRegion
import yaExpandRegion
reload(yaExpandRegion)

getNextRegion = yaExpandRegion.getNextRegion
fixture = None

class TestFunctions(TestCase):
  @classmethod
  def setUpClass(cls):
    global fixture
    file = open(f'{currentDir}/fixture1.js', 'r')
    fixture = file.read()
    file.close()

  def test_1(self):
    """match outer {...} and braket itself"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(1,1)), sublime.Region(1,176))
    self.assertEqual(getNextRegion(fixture, sublime.Region(0,0)), sublime.Region(0,177))
  def test_2(self):
    """match {}"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(48,48)), sublime.Region(47,49))
  def test_3(self):
    """match one char Region { }"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(60,60)), sublime.Region(60,61))
    self.assertEqual(getNextRegion(fixture, sublime.Region(61,61)), sublime.Region(60,61))
  def test_4(self):
    """match []"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(202,202)), sublime.Region(202,212))
  def test_5(self):
    """match ()"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(248,248)), sublime.Region(248,320))
  def test_6(self):
    """not empty selection"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(60,61)), sublime.Region(59,62))
  
  def test_7(self):
    """match double quote \"some text\" outer and inner """
    self.assertEqual(getNextRegion(fixture, sublime.Region(325,325)), sublime.Region(325,337))
    self.assertEqual(getNextRegion(fixture, sublime.Region(325,337)), sublime.Region(324,338))
  def test_8(self):
    """match non capturing string while selection inside [...]"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(349,349)), sublime.Region(341,388))
  def test_9(self):
    """match [...] inside capturing string"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(410,410)), sublime.Region(408,415))
  def test_9_1(self):
    """match capturing string outer and inner"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(403,403)), sublime.Region(391,433))
    self.assertEqual(getNextRegion(fixture, sublime.Region(391,433)), sublime.Region(390,434))

  def test_10(self):
    """match full tag at start of tagHead"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(501,501)), sublime.Region(501,546))
  def test_11(self):
    """match string in tagHead"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(514,514)), sublime.Region(513,517))
  def test_12(self):
    """match text in tag"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(531,531)), sublime.Region(531,540))
  def test_13(self):
    """match full tag at tagTail"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(541,541)), sublime.Region(501,546))

  def test_14(self):
    """match nested tag content"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(612,653)), sublime.Region(605,658))
  def test_15(self):
    """match nested tag"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(605,658)), sublime.Region(597,667))
  def test_16(self):
    """match <Provider>...</> content"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(597,667)), sublime.Region(592,738))
  def test_17(self):
    """match <SingleTag />"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(672,672)), sublime.Region(672,735))
  def test_18(self):
    """match <Provider.Context ...> content and tag itself"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(804,874)), sublime.Region(799,899))
    self.assertEqual(getNextRegion(fixture, sublime.Region(799,899)), sublime.Region(763,918))
  def test_19(self):
    """match fragment <>...</> content and itself"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(888,888)), sublime.Region(881,893))
    self.assertEqual(getNextRegion(fixture, sublime.Region(881,893)), sublime.Region(879,896))

  def test_20(self):
    """match nested divs <div><div>...</div></div>"""
    self.assertEqual(getNextRegion(fixture, sublime.Region(978,978)), sublime.Region(978,1019))
    self.assertEqual(getNextRegion(fixture, sublime.Region(978,1019)), sublime.Region(971,1024))
    self.assertEqual(getNextRegion(fixture, sublime.Region(971,1024)), sublime.Region(966,1030))
    self.assertEqual(getNextRegion(fixture, sublime.Region(966,1030)), sublime.Region(961,1033))
    self.assertEqual(getNextRegion(fixture, sublime.Region(961,1033)), sublime.Region(938,1039))
