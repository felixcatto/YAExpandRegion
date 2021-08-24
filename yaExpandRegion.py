import sublime
import sublime_plugin
import re
from functools import reduce


def getNextRegion(text, selection):
  openBracketChars = ['{', '[', '(']
  closeBracketChars = ['}', ']', ')']
  stringChars = ['`', '"', '\'']
  capturingStringSymbol = '`'
  tagStartSymbol = '<'
  tagEndSymbol = '>'
  braketIndexes = []
  regionsForExpand = []
  lastStringIndex = None
  lastStringChar = None
  tags = []

  for i in range(0, len(text)):
    char = text[i]
    isInNonCapturingString = lastStringIndex and lastStringChar != capturingStringSymbol

    if isInNonCapturingString:
      # end for simpleStr
      if char == lastStringChar:
        isEmptyRegion = lastStringIndex + 1 == i
        regionsForExpand.append(sublime.Region(lastStringIndex, i + 1))
        if not isEmptyRegion:
          regionsForExpand.append(sublime.Region(lastStringIndex + 1, i))
        lastStringIndex = None
        lastStringChar = None
      continue    

    if char in stringChars:
      if not lastStringIndex:
        # start for simpleStr and capturingStr
        lastStringIndex = i
        lastStringChar = char
      elif lastStringIndex and char == lastStringChar:
        # end for capturingStr
        isEmptyRegion = lastStringIndex + 1 == i
        regionsForExpand.append(sublime.Region(lastStringIndex, i + 1))
        if not isEmptyRegion:
          regionsForExpand.append(sublime.Region(lastStringIndex + 1, i))
        lastStringIndex = None
        lastStringChar = None
    elif char in openBracketChars:
      braketIndexes.append(i)
    elif char in closeBracketChars:
      lastOpenTokenIndex = braketIndexes.pop()
      isEmptyRegion = lastOpenTokenIndex + 1 == i
      regionsForExpand.append(sublime.Region(lastOpenTokenIndex, i + 1))
      if not isEmptyRegion:
        regionsForExpand.append(sublime.Region(lastOpenTokenIndex + 1, i))
    elif char == tagStartSymbol:
      textPart = text[i:]
      lastTag = tags and tags[-1]
      isTagAhead = re.match(r'<(\w+(?:\.\w+)?).*?>.*?</\1>', textPart, re.S)
      isSingleTagAhead = re.match(r'<\w+[^<]*?/>', textPart, re.S)
      isFragmentTagAhead = re.match(r'<>.*?</>', textPart, re.S)
      isTagTailAhead = lastTag and not lastTag['tagTailStart'] and re.match(f'</{lastTag["tagName"]}>', textPart, re.S)
      if isTagAhead or isFragmentTagAhead:
        tagName = isTagAhead.group(1) if isTagAhead else ''
        tag = {
          'tagName': tagName,
          'tagHeadStart': i,
          'tagHeadEnd': None,
          'tagTailStart': None,
          'tagTailEnd': None,
        }
        tags.append(tag)
      elif isSingleTagAhead:
        tag = {
          'tagHeadStart': i,
          'tagTailEnd': i + isSingleTagAhead.end(0) - 1,
        }
        regionsForExpand.append(sublime.Region(tag['tagHeadStart'], tag['tagTailEnd'] + 1))
      elif isTagTailAhead:
        lastTag['tagTailStart'] = i
    elif char == tagEndSymbol:
      lastTag = tags and tags[-1]
      if not lastTag: continue

      if not lastTag['tagHeadEnd']:
        lastTag['tagHeadEnd'] = i
      elif lastTag['tagHeadEnd'] and lastTag['tagTailStart']:
        lastTag['tagTailEnd'] = i
        regionsForExpand.append(sublime.Region(lastTag['tagHeadStart'], lastTag['tagTailEnd'] + 1))
        regionsForExpand.append(sublime.Region(lastTag['tagHeadEnd'] + 1, lastTag['tagTailStart']))
        tags = tags[0:-1]

  containingCurlyRegions = list(filter(lambda el: el.contains(selection) and el != selection, regionsForExpand))
  if not containingCurlyRegions:
    return None

  closestContainingRegion = reduce(lambda acc, el: el if el.size() < acc.size() else acc, containingCurlyRegions)
  return closestContainingRegion

def getPosition(view):
  return view.sel()[0].begin()

class ExampleCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    view = self.view
    selection = view.sel()[0]
    text = view.substr(sublime.Region(0, view.size())) 
    closestContainingRegion = getNextRegion(text, selection)
    if not closestContainingRegion:
      sublime.status_message('Can\'t expand')
      return
    print(f'match -> {closestContainingRegion}')
    view.sel().add(closestContainingRegion)

class ExampleEventListener(sublime_plugin.ViewEventListener):
  @classmethod
  def is_applicable(self, settings):
    return 'JSX.sublime-syntax' in settings.get('syntax')
  def on_selection_modified(self):
    view = self.view
    selection = view.sel()[0]
    print(selection)
