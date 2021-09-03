import sublime
import sublime_plugin
import re
from functools import reduce


cachedRegionsForExpand = None

def some(array, filterFn):
  for el in array:
    if filterFn(el):
      return True
  return False

def getNextRegion(text, selection, options = {}):
  cachedRegionsForExpand = options.get("cachedRegionsForExpand") or None
  commentsRegions = options.get("commentsRegions") or []

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
    return getNextContainingRegion(regionsForExpand, selection)

  openBracketChars = ['{', '[', '(']
  closeBracketChars = ['}', ']', ')']
  stringChars = ['`', '"', '\'']
  capturingStringSymbol = '`'
  braketIndexes = []
  lastStringIndex = None
  lastStringChar = None

  for i in range(0, len(text)):
    char = text[i]
    isInNonCapturingString = lastStringIndex and lastStringChar != capturingStringSymbol
    isInComment = some(commentsRegions, lambda el: el.contains(i))
    if isInComment:
      continue

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

  return getNextContainingRegion(regionsForExpand, selection)

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

def getNextContainingRegion(regionsForExpand, selection):
  containingRegions = list(filter(lambda el: el.contains(selection) and el != selection, regionsForExpand))
  if not containingRegions:
    return [None, regionsForExpand]

  nextContainingRegion = reduce(lambda acc, el: el if el.size() < acc.size() else acc, containingRegions)
  return [nextContainingRegion, regionsForExpand]

class YaexpandRegionCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    global cachedRegionsForExpand
    view = self.view
    selection = view.sel()[0]
    text = view.substr(sublime.Region(0, view.size()))
    mapFn = lambda region: sublime.Region(region.begin(), region.end() - 1)
    commentsRegions = list(map(mapFn, view.find_by_selector('comment')))
    nextContainingRegion, regionsForExpand = getNextRegion(text, selection, {
      'cachedRegionsForExpand': cachedRegionsForExpand,
      'commentsRegions': commentsRegions,
    })
    cachedRegionsForExpand = regionsForExpand
    if not nextContainingRegion:
      return sublime.status_message('Can\'t expand')
    addFn = lambda: view.sel().add(nextContainingRegion)
    addFn()
    sublime.set_timeout(addFn, 0) # hack to make soft undo works

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
