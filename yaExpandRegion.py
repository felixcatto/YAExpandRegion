import sublime
import sublime_plugin
import re
from functools import reduce


cachedRegionsForExpand = None
initialSelection = None
# After we set 'initialSelection', we run selectionAdd and then 'selection_modified' event happens
# The problem is we also need to clear 'initialSelection' whenever this event happens
# So we set 'initialSelection', and then immediately clear it :face-palm:
# And to prevent it we introduce this clumsy variables
canSkipModifiedEvent = True
initialSelectionStatus = 'notSet' # 'notSet' | 'setAndUnsetDisabled' | 'set'

def resetInitialSelection():
  global initialSelection, initialSelectionStatus, canSkipModifiedEvent
  initialSelection = None
  initialSelectionStatus = 'notSet'
  canSkipModifiedEvent = True

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

def getPreviousRegion(regionsForExpand, selection, initialSelection):
  filterFn = lambda el: selection.contains(el) and el != selection and el.contains(initialSelection)
  containingRegions = list(filter(filterFn, regionsForExpand))
  if not containingRegions:
    return None

  nextChildRegion = reduce(lambda acc, el: el if el.size() > acc.size() else acc, containingRegions)
  return nextChildRegion

class YaexpandRegionCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    global cachedRegionsForExpand, initialSelection, initialSelectionStatus, canSkipModifiedEvent
    view = self.view
    selection = view.sel()[0]
    text = view.substr(sublime.Region(0, view.size()))
    nextContainingRegion, regionsForExpand = getNextRegion(text, selection, {
      'cachedRegionsForExpand': cachedRegionsForExpand,
    })
    cachedRegionsForExpand = regionsForExpand
    if not nextContainingRegion:
      return sublime.status_message('Can\'t expand')

    initialSelectionStatus = 'setAndUnsetDisabled'
    if initialSelection is None:
      initialSelection = selection
      canSkipModifiedEvent = False
    view.sel().add(nextContainingRegion)

class YaexpandUndoCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    global cachedRegionsForExpand, initialSelection, initialSelectionStatus
    view = self.view
    selection = view.sel()[0]
    nextChildRegion = getPreviousRegion(cachedRegionsForExpand, selection, initialSelection)
    if not nextChildRegion:
      return sublime.status_message('Can\'t undo')
    initialSelectionStatus = 'setAndUnsetDisabled'
    view.sel().clear()
    view.sel().add(nextChildRegion)

class ExampleEventListener(sublime_plugin.ViewEventListener):
  def on_modified(self):
    global cachedRegionsForExpand
    if cachedRegionsForExpand:
      cachedRegionsForExpand = None
      resetInitialSelection()
  def on_deactivated(self):
    global cachedRegionsForExpand
    if cachedRegionsForExpand:
      cachedRegionsForExpand = None
      resetInitialSelection()
  def on_selection_modified(self):
    # print(self.view.sel()[0])
    global initialSelectionStatus, canSkipModifiedEvent
    if canSkipModifiedEvent: return
    if initialSelectionStatus == 'setAndUnsetDisabled':
      initialSelectionStatus = 'set'
    elif initialSelectionStatus == 'set':
      resetInitialSelection()
