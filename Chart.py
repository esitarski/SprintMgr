import wx
import wx.grid as gridlib

import os
import sys
import six
import Utils
from ReorderableGrid import ReorderableGrid, GridCellMultiLineStringRenderer
from Competitions import SetDefaultData
import Model
from Utils import WriteCell
from Events import GetFont

class Chart(wx.Panel):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		
		font = GetFont()

		self.title = wx.StaticText(self, wx.ID_ANY, "Competition Table:")
		self.title.SetFont( font )
		self.showNames = wx.ToggleButton( self, wx.ID_ANY, 'Show Names' )
		self.showNames.SetFont( font )
		self.showNames.Bind( wx.EVT_TOGGLEBUTTON, self.onToggleShow )
		self.showTeams = wx.ToggleButton( self, wx.ID_ANY, 'Show Teams' )
		self.showTeams.SetFont( font )
		self.showTeams.Bind( wx.EVT_TOGGLEBUTTON, self.onToggleShow ) 

		self.headerNames = ['', 'System', 'Event', 'Heats', 'In', 'Bib', 'Name', 'Team', 'H1', 'H2', 'H3', 'Out', 'Bib', 'Name', 'Team']
		self.numericFields = set( ['Event', 'Heats', 'Bib', 'In', 'Out'] )
		
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.DisableDragRowSize()
		self.grid.SetRowLabelSize( 0 )
		self.grid.EnableReorderRows( False )
		self.grid.CreateGrid( 0, len(self.headerNames) )
		self.setColNames()
		
		# Set a larger font for the table.
		# Set specialized editors for appropriate columns.
		self.grid.SetLabelFont( font )
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		hs = wx.BoxSizer( wx.HORIZONTAL )
		hs.Add( self.title, 0, flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL, border = 4 )
		hs.Add( self.showNames, 0, flag=wx.ALL, border = 4 )
		hs.Add( self.showTeams, 0, flag=wx.ALL, border = 4 )
		
		sizer.Add( hs, flag=wx.ALL, border = 4 )
		sizer.Add(self.grid, 1, flag=wx.EXPAND|wx.ALL, border = 6)
		self.SetSizer(sizer)
		
	def onToggleShow( self, e ):
		model = Model.model
		model.chartShowNames = self.showNames.GetValue()
		model.chartShowTeams = self.showTeams.GetValue()
		self.refresh()
	
	def getHideCols( self, headerNames ):
		model = Model.model
		toHide = set()
		for col, h in enumerate(headerNames):
			if h == 'Name' and not getattr(model, 'chartShowNames', True):
				toHide.add( col )
			elif h == 'Team' and not getattr(model, 'chartShowTeams', True):
				toHide.add( col )
		return toHide
	
	def setColNames( self ):
		for col, headerName in enumerate(self.headerNames):
			self.grid.SetColLabelValue( col, headerName )
						
	def getGrid( self ):
		return self.grid
		
	def refresh( self ):
		model = Model.model
		competition = model.competition
		state = competition.state
		
		self.showNames.SetValue( getattr(model, 'chartShowNames', True) )
		self.showTeams.SetValue( getattr(model, 'chartShowTeams', True) )
		
		font = GetFont()

		self.headerNames = ['', 'System', 'Event', 'Heats', 'In', 'Bib', 'Name', 'Team', 'H1', 'H2', 'H3', 'Out', 'Bib', 'Name', 'Team']
		hideCols = self.getHideCols( self.headerNames )
		self.headerNames = [h for c, h in enumerate(self.headerNames) if c not in hideCols]
		Utils.AdjustGridSize( self.grid, rowsRequired = sum(1 for t,s,e in competition.allEvents()), colsRequired = len(self.headerNames) )
		self.grid.ClearGrid()
		self.setColNames()
		
		for col in six.moves.range(self.grid.GetNumberCols()):
			attr = gridlib.GridCellAttr()
			attr.SetFont( font )
			attr.SetReadOnly( True )
			if col >= 4:
				attr.SetRenderer( GridCellMultiLineStringRenderer() )
			if self.headerNames[col] in self.numericFields:
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP )
			elif self.headerNames[col].startswith( 'H' ):
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP )
			self.grid.SetColAttr( col, attr )
		
		row = 0
		for tournament in competition.tournaments:
			self.grid.SetCellValue( row, 0, tournament.name )
			for system in tournament.systems:
				self.grid.SetCellValue( row, 1, system.name )
				for i, event in enumerate(system.events):
					writeCell = WriteCell( self.grid, row, 2 )
					
					writeCell( u'{}'.format(i+1) )
					writeCell(u' {}'.format(event.heatsMax) )
					writeCell( u'\n'.join(event.composition).replace(u'\n',u' ({})\n'.format(len(event.composition)),1) )
					
					riders = [state.labels.get(c, None) for c in event.composition]
					writeCell( u'\n'.join([u'{}'.format(rider.bib if rider.bib else u'') if rider else '' for rider in riders]) )
					if getattr(model, 'chartShowNames', True):
						writeCell( u'\n'.join([rider.full_name if rider else u'' for rider in riders]) )
					if getattr(model, 'chartShowTeams', True):
						writeCell( u'\n'.join([rider.team if rider else u'' for rider in riders]) )
					
					for heat in six.moves.range(3):
						if event.heatsMax > 1:
							writeCell( u'\n'.join(event.getHeatPlaces(heat+1)) )
						else:
							writeCell( u'' )
					
					out = [event.winner] + event.others
					writeCell( u'\n'.join(out).replace(u'\n',u' ({})\n'.format(len(out)),1) )
					riders = [state.labels.get(c, None) for c in out]
					writeCell( u'\n'.join([u'{}'.format(rider.bib if rider.bib else '') if rider else '' for rider in riders]) )
					if getattr(model, 'chartShowNames', True):
						writeCell( '\n'.join([rider.full_name if rider else '' for rider in riders]) )
					if getattr(model, 'chartShowTeams', True):
						writeCell( '\n'.join([rider.team if rider else '' for rider in riders]) )
					row += 1
					
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )
		
	def commit( self ):
		pass
		
########################################################################

class ChartFrame(wx.Frame):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		wx.Frame.__init__(self, None, title="Chart Grid Test", size=(1000,800) )
		self.panel = Chart(self)
		self.Show()
 
#----------------------------------------------------------------------
if __name__ == "__main__":
	app = wx.App(False)
	Model.model = SetDefaultData()
	frame = ChartFrame()
	frame.panel.refresh()
	app.MainLoop()
