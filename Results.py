import wx
import wx.grid as gridlib

import os
import sys
import six
import TestData
import Model
import Utils
from ReorderableGrid import ReorderableGrid
from Competitions import SetDefaultData
from Utils import WriteCell
from Events import FontSize

Arrow = u'\u2192'

class Results(wx.Panel):
	#----------------------------------------------------------------------
	def __init__(self, parent):
		"""Constructor"""
		wx.Panel.__init__(self, parent)
 
		self.font = wx.Font( (0,FontSize), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL )
		
		self.showResultsLabel = wx.StaticText( self, wx.ID_ANY, u'Show:' )
		self.showResultsLabel.SetFont( self.font )
		self.showResults = wx.Choice( self, wx.ID_ANY, choices = ['Qualifiers'] )
		self.showResults.SetFont( self.font )
		self.showResults.SetSelection( 0 )
		
		self.communiqueLabel = wx.StaticText( self, wx.ID_ANY, u'Communiqu\u00E9:' )
		self.communiqueLabel.SetFont( self.font )
		self.communiqueNumber = wx.TextCtrl( self, wx.ID_ANY, '', size=(80,-1) )
		self.communiqueNumber.SetFont( self.font )
		
		self.showResults.Bind( wx.EVT_LEFT_DOWN, self.onClickResults )
		self.showResults.Bind( wx.EVT_CHOICE, self.onShowResults )
		self.showNames = wx.ToggleButton( self, wx.ID_ANY, u'Show Names' )
		self.showNames.SetFont( self.font )
		self.showNames.Bind( wx.EVT_TOGGLEBUTTON, self.onToggleShow )
		self.showTeams = wx.ToggleButton( self, wx.ID_ANY, u'Show Teams' )
		self.showTeams.SetFont( self.font )
		self.showTeams.Bind( wx.EVT_TOGGLEBUTTON, self.onToggleShow )
		self.competitionTime = wx.StaticText( self )
 
		self.headerNames = ['uPos', u'Bib', u'Rider', u'Team', u'License']
		
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.DisableDragRowSize()
		self.grid.SetRowLabelSize( 64 )
		self.grid.CreateGrid( 0, len(self.headerNames) )
		self.grid.SetRowLabelSize( 0 )
		self.grid.EnableReorderRows( False )
		self.setColNames()

		sizer = wx.BoxSizer(wx.VERTICAL)
		
		hs = wx.BoxSizer(wx.HORIZONTAL)
		hs.Add( self.showResultsLabel, 0, flag=wx.ALIGN_CENTRE_VERTICAL, border = 4 )
		hs.Add( self.showResults, 0, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4 )
		hs.Add( self.communiqueLabel, 0, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4 )
		hs.Add( self.communiqueNumber, 0, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, border = 4 )
		hs.Add( self.showNames, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4 )
		hs.Add( self.showTeams, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4 )
		hs.Add( self.competitionTime, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4 )
		
		sizer.Add(hs, 0, flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border = 6 )
		sizer.Add(self.grid, 1, flag=wx.EXPAND|wx.ALL, border = 6)
		self.SetSizer(sizer)
	
	def onToggleShow( self, e ):
		model = Model.model
		model.resultsShowNames = self.showNames.GetValue()
		model.resultsShowTeams = self.showTeams.GetValue()
		self.refresh()
	
	def setColNames( self ):
		self.grid.SetLabelFont( self.font )
		for col, headerName in enumerate(self.headerNames):
			self.grid.SetColLabelValue( col, headerName )
			
			attr = gridlib.GridCellAttr()
			attr.SetFont( self.font )
			if self.headerNames[col] in {u'Bib', u'Event'}:
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP )
			elif u'Time' in self.headerNames[col]:
				attr.SetAlignment( wx.ALIGN_RIGHT, wx.ALIGN_TOP )
			elif self.headerNames[col] == u'Pos':
				attr.SetAlignment( wx.ALIGN_RIGHT, wx.ALIGN_TOP )
			elif Arrow in self.headerNames[col]:
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_VERTICAL_CENTRE )
			elif self.headerNames[col].startswith( u'H' ):
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP )
			attr.SetReadOnly( True )
			self.grid.SetColAttr( col, attr )
	
	def getResultChoices( self ):
		model = Model.model
		competition = model.competition
		choices = [u'Qualifiers']
		for tournament in competition.tournaments:
			for system in tournament.systems:
				name = ('%s: ' % tournament.name if tournament.name else '') + system.name
				choices.append( name )
		choices.append( u'Final Classification' )
		return choices
	
	def fixShowResults( self ):
		model = Model.model
		competition = model.competition
		
		choices = self.getResultChoices()
		self.showResults.SetItems( choices )
		
		if model.showResults >= len(choices):
			model.showResults = 0
		self.showResults.SetSelection( model.showResults )
		
	def getHideCols( self, headerNames ):
		model = Model.model
		toHide = set()
		for col, h in enumerate(headerNames):
			if h == u'Name' and not getattr(model, 'resultsShowNames', True):
				toHide.add( col )
			elif h == u'Team' and not getattr(model, 'resultsShowTeams', True):
				toHide.add( col )
		return toHide
	
	def getGrid( self ):
		return self.grid
	
	def getPhase( self, num = None ):
		if num is None:
			num = self.showResults.GetSelection()
		choices = self.getResultChoices()
		return choices[num]
	
	def getTitle( self ):
		phase = self.getPhase()
		title = u'Communiqu\u00E9: {}\n{} {} '.format(
					self.communiqueNumber.GetValue(),
					phase,
					'' if phase.startswith(u'Final') or phase.startswith('Time') else u'Draw Sheet/Intermediate Results' )
		return title
	
	def onClickResults( self, event ):
		self.commit()
		event.Skip()
		
	def onShowResults( self, event ):
		Model.model.showResults = self.showResults.GetSelection()
		self.refresh()
	
	def refresh( self ):
		self.fixShowResults()
		self.grid.ClearGrid()
		
		model = Model.model
		competition = model.competition
		
		self.showNames.SetValue( getattr(model, 'resultsShowNames', True) )
		self.showTeams.SetValue( getattr(model, 'resultsShowTeams', True) )
		
		self.communiqueNumber.SetValue( model.communique_number.get(self.getPhase(), '') )
		
		resultName = self.showResults.GetStringSelection()
		
		if 'Qualifiers' in resultName:
			starters = competition.starters
			
			self.headerNames = [u'Pos', u'Bib', u'Name', u'Team', u'Time']
			hideCols = self.getHideCols( self.headerNames )
			self.headerNames = [h for c, h in enumerate(self.headerNames) if c not in hideCols]
			
			riders = sorted( model.riders, key = lambda r: r.keyQualifying() )
			for row, r in enumerate(riders):
				if row >= starters or r.status == 'DNQ':
					riders[row:] = sorted( riders[row:], key=lambda r: r.keyQualifying()[1:] )
					break
			Utils.AdjustGridSize( self.grid, rowsRequired = len(riders), colsRequired = len(self.headerNames) )
			Utils.SetGridCellBackgroundColour( self.grid, wx.WHITE )
			self.setColNames()
			for row, r in enumerate(riders):
				if row < starters and r.status != 'DNQ':
					pos = u'{}'.format(row + 1)
					for col in six.moves.range(self.grid.GetNumberCols()):
						self.grid.SetCellBackgroundColour( row, col, wx.WHITE )
				else:
					pos = 'DNQ'
					for col in six.moves.range(self.grid.GetNumberCols()):
						self.grid.SetCellBackgroundColour( row, col, wx.Colour(200,200,200) )
						
				writeCell = WriteCell( self.grid, row )
				for col, value in enumerate([pos,u' {}'.format(r.bib), r.full_name, r.team, r.qualifyingTimeText]):
					if col not in hideCols:
						writeCell( value )
						
			competitionTime = model.qualifyingCompetitionTime
			self.competitionTime.SetLabel( u'{}: {}'.format(_('Est. Competition Time'), Utils.formatTime(competitionTime)) 
				if competitionTime else u'' )
					
		elif 'Final Classification' in resultName:
			self.headerNames = [u'Pos', u'Bib', u'Name', u'Team', u'License']
			hideCols = self.getHideCols( self.headerNames )
			self.headerNames = [h for c, h in enumerate(self.headerNames) if c not in hideCols]
			
			results, dnfs, dqs = competition.getResults()
			Utils.AdjustGridSize( self.grid, rowsRequired = len(model.riders), colsRequired = len(self.headerNames) )
			Utils.SetGridCellBackgroundColour( self.grid, wx.WHITE )

			self.setColNames()
			for row, (classification, r) in enumerate(results):
				writeCell = WriteCell( self.grid, row )
				if not r:
					for col in six.moves.range(self.grid.GetNumberCols()):
						writeCell( '' )
				else:
					for col, value in enumerate([classification, r.bib if r.bib else '', r.full_name, r.team, r.license]):
						if col not in hideCols:
							writeCell(u' {}'.format(value) )
			self.competitionTime.SetLabel( u'' ) 
		else:
			# Find the Tournament and System selected.
			keepGoing = True
			for tournament in competition.tournaments:
				for system in tournament.systems:
					name = (u'%s: ' % tournament.name if tournament.name else '') + system.name
					if name == resultName:
						keepGoing = False
						break
				if not keepGoing:
					break
			
			heatsMax = max( event.heatsMax for event in system.events )
			if heatsMax == 1:
				self.headerNames = [u'Event',u'Bib',u'Name',u'Note',u'Team',u'    ',u'Pos',u'Bib',u'Name',u'Note',u'Team',u'Time']
			else:
				self.headerNames = [u'Event',u'Bib',u'Name',u'Note',u'Team',u'H1',u'H2',u'H3',u'    ',u'Pos',u'Bib',u'Name',u'Note',u'Team',u'Time']
			hideCols = self.getHideCols( self.headerNames )
			self.headerNames = [h for c, h in enumerate(self.headerNames) if c not in hideCols]
			
			Utils.AdjustGridSize( self.grid, rowsRequired = len(system.events), colsRequired = len(self.headerNames) )
			Utils.SetGridCellBackgroundColour( self.grid, wx.WHITE )

			self.setColNames()
			state = competition.state
			
			for row, event in enumerate(system.events):
				writeCell = WriteCell( self.grid, row )
				
				writeCell( u'{}'.format(row+1) )
				
				riders = [state.labels.get(c, None) for c in event.composition]
				writeCell( u'\n'.join([u'{}'.format(rider.bib) if rider and rider.bib else '' for rider in riders]) )
				if getattr(model, 'resultsShowNames', True):
					writeCell( u'\n'.join([rider.full_name  if rider else u'' for rider in riders]) )
				writeCell( u'\n'.join([competition.getRelegationsWarningsStr(rider.bib, event, True) if rider else u'' for rider in riders]) )
				if getattr(model, 'resultsShowTeams', True):
					writeCell( u'\n'.join([rider.team if rider else '' for rider in riders]) )

				if heatsMax != 1:
					for heat in six.moves.range(heatsMax):
						if event.heatsMax != 1:
							writeCell( u'\n'.join(event.getHeatPlaces(heat+1)) )
						else:
							writeCell( u'' )
				
				#writeCell( u' ===> ', vert=wx.ALIGN_CENTRE )
				writeCell( ' '.join(['',Arrow,'']), vert=wx.ALIGN_CENTRE )
				
				out = [event.winner] + event.others
				riders = [state.labels.get(c, None) for c in out]
				writeCell( u'\n'.join( u'{}'.format(i+1) for i in six.moves.range(len(riders))) )
				writeCell( u'\n'.join([u'{}'.format(rider.bib if rider.bib else '') if rider else '' for rider in riders]) )
				if getattr(model, 'resultsShowNames', True):
					writeCell( u'\n'.join([rider.full_name if rider else '' for rider in riders]) )
				writeCell( u'\n'.join([competition.getRelegationsWarningsStr(rider.bib, event, False) if rider else u'' for rider in riders]) )
				if getattr(model, 'resultsShowTeams', True):
					writeCell( u'\n'.join([rider.team if rider else '' for rider in riders]) )
				if event.winner in state.labels:
					try:
						value = u'%.3f' % event.starts[-1].times[1]
					except (KeyError, IndexError, ValueError):
						value = ''
					writeCell( value )
			
			competitionTime = system.competitionTime
			self.competitionTime.SetLabel( u'{}: {}'.format(_('Est. Competition Time'), Utils.formatTime(competitionTime)) 
				if competitionTime else u'' )
		
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )
		
	def commit( self ):
		model = Model.model
		phase = self.getPhase()
		cn = self.communiqueNumber.GetValue()
		if cn != model.communique_number.get(phase, u''):
			model.communique_number[phase] = cn
			model.setChanged()
		
########################################################################

class ResultsFrame(wx.Frame):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		wx.Frame.__init__(self, None, title="Results Grid Test", size=(800,600) )
		panel = Results(self)
		panel.refresh()
		self.Show()
 
#----------------------------------------------------------------------
if __name__ == "__main__":
	app = wx.App(False)
	Model.model = SetDefaultData()
	frame = ResultsFrame()
	app.MainLoop()
