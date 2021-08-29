import sublime
import sublime_plugin
import re
from functools import reduce


cachedRegionsForExpand = None

def getNextRegion(text, selection, options = {}):
  cachedRegionsForExpand = options.get("cachedRegionsForExpand") or None

  regionsForExpand = cachedRegionsForExpand or []
  shouldExpandToWord = selection.begin() == selection.end()
  if shouldExpandToWord:
    point = selection.begin()
    wordBoundaries = []
    backWord = re.search(r'(\$?\b\w+)$', text[:point])
    foreWord = re.match(r'^(\w+\b\$?)', text[point:])
    if backWord:
      wordBoundaries.append(backWord.start())
      wordBoundaries.append(point - 1)
    if foreWord:
      wordBoundaries.append(point)
      wordBoundaries.append(point + foreWord.end() - 1)
    if wordBoundaries:
      wordRegion = sublime.Region(min(wordBoundaries), max(wordBoundaries) + 1);
      return [wordRegion, regionsForExpand]
  if cachedRegionsForExpand:
    return getClosestContainingRegion(regionsForExpand, selection)

  openBracketChars = ['{', '[', '(']
  closeBracketChars = ['}', ']', ')']
  stringChars = ['`', '"', '\'']
  capturingStringSymbol = '`'
  tagStartSymbol = '<'
  tagEndSymbol = '>'
  braketIndexes = []
  lastStringIndex = None
  lastStringChar = None
  tags = []

  for i in range(0, len(text)):
    char = text[i]
    isInNonCapturingString = lastStringIndex and lastStringChar != capturingStringSymbol

    if isInNonCapturingString:
      # end for simpleStr
      if isCharEscaped(text, i): continue
      if char == lastStringChar:
        isEmptyRegion = lastStringIndex + 1 == i
        regionsForExpand.append(sublime.Region(lastStringIndex, i + 1))
        if not isEmptyRegion:
          regionsForExpand.append(sublime.Region(lastStringIndex + 1, i))
        lastStringIndex = None
        lastStringChar = None
      continue    

    if char in stringChars:
      if isCharEscaped(text, i): continue
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

  return getClosestContainingRegion(regionsForExpand, selection)

def isCharEscaped(text, i):
  escapeSymbol = '\\'
  if i == 0 : return False
  if text[i - 1] != escapeSymbol:
    return False
  elif i == 1 and text[i - 1] == escapeSymbol:
    return True
  else:
    isFirstEscapeSymbol = text[i - 1] == escapeSymbol
    isSecondEscapeSymbol = text[i - 2] == escapeSymbol
    if isFirstEscapeSymbol and not isSecondEscapeSymbol:
      return True
    else:
      return False

def getClosestContainingRegion(regionsForExpand, selection):
  containingRegions = list(filter(lambda el: el.contains(selection) and el != selection, regionsForExpand))
  if not containingRegions:
    return [None, regionsForExpand]

  closestContainingRegion = reduce(lambda acc, el: el if el.size() < acc.size() else acc, containingRegions)
  return [closestContainingRegion, regionsForExpand]

def getPosition(view):
  return view.sel()[0].begin()

class YaexpandRegionCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    global cachedRegionsForExpand
    view = self.view
    selection = view.sel()[0]
    text = view.substr(sublime.Region(0, view.size()))
    closestContainingRegion, regionsForExpand = getNextRegion(text, selection, {
      'cachedRegionsForExpand': cachedRegionsForExpand,
    })
    cachedRegionsForExpand = regionsForExpand
    if not closestContainingRegion:
      sublime.status_message('Can\'t expand')
      return
    view.sel().add(closestContainingRegion)

class ExampleEventListener(sublime_plugin.ViewEventListener):
  def on_modified(self):
    global cachedRegionsForExpand
    if cachedRegionsForExpand:
      cachedRegionsForExpand = None
  def on_deactivated(self):
    global cachedRegionsForExpand
    if cachedRegionsForExpand:
      cachedRegionsForExpand = None
  # def on_selection_modified(self):
  #   print(self.view.sel()[0])
