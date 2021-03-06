import wx
import wx.grid as gridlib

import os
import sys
import six
import TestData
import Utils
import Model
from Competitions import SetDefaultData
from ReorderableGrid import ReorderableGrid
from Events import GetFont
from HighPrecisionTimeEditor import HighPrecisionTimeEditor

#--------------------------------------------------------------------------------
class Qualifiers(wx.Panel):

	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
 
		font = GetFont()
		self.title = wx.StaticText(self, wx.ID_ANY, "Enter each rider's qualifying time in hh:mm:ss.ddd format.  Use a colon ':' a space, or a dash '-' to separate hour, minute and seconds.")
		self.title.SetFont( font )
		
		self.renumberButton = wx.Button( self, wx.ID_ANY, 'Renumber Bibs by Time' )
		self.renumberButton.SetFont( font )
		self.renumberButton.Bind( wx.EVT_BUTTON, self.doRenumber )
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		hs.Add( self.title, 0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border = 6 )
		hs.AddStretchSpacer()
		hs.Add( self.renumberButton, 0, flag=wx.ALL, border = 6 )
 
		self.headerNames = ['Bib', 'Name', 'Team', 'Time', 'Status']
		self.iTime = next( i for i, n in enumerate(self.headerNames) if n.startswith( 'Time' ) )
		self.iStatus = next( i for i, n in enumerate(self.headerNames) if n.startswith( 'Status' ) )
		
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.DisableDragRowSize()
		self.grid.SetRowLabelSize( 64 )
		self.grid.CreateGrid( 0, len(self.headerNames) )
		self.setColNames()
		self.grid.EnableReorderRows( False )

		# Set specialized editors for appropriate columns.
		self.grid.SetLabelFont( font )
		for col in six.moves.range(self.grid.GetNumberCols()):
			attr = gridlib.GridCellAttr()
			attr.SetFont( font )
			if col == self.iTime:
				attr.SetEditor( HighPrecisionTimeEditor() )
				attr.SetAlignment( wx.ALIGN_RIGHT, wx.ALIGN_CENTRE )
			elif col == self.iStatus:
				attr.SetEditor( gridlib.GridCellChoiceEditor(choices = ['', 'DNQ']) )
				attr.SetReadOnly( False )
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
			else:
				if col == 0:
					attr.SetRenderer( gridlib.GridCellNumberRenderer() )
				attr.SetReadOnly( True )
			self.grid.SetColAttr( col, attr )
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add( hs, 0, flag=wx.ALL|wx.EXPAND, border = 6 )
		sizer.Add(self.grid, 1, flag=wx.EXPAND|wx.ALL, border = 6)
		self.SetSizer(sizer)
		
	def getGrid( self ):
		return self.grid
		
	def setColNames( self ):
		for col, headerName in enumerate(self.headerNames):
			self.grid.SetColLabelValue( col, headerName )
						
	def setTestData( self ):
		self.grid.ClearGrid()

		testData = TestData.getTestData()
		Utils.AdjustGridSize( self.grid, rowsRequired = len(testData) )
			
		for row, data in enumerate(testData):
			bib = data[0]
			name = data[1] + ' ' + data[2]
			team = data[3]
			time = data[-1]
			for col, d in enumerate([bib, name, team, time]):
				self.grid.SetCellValue( row, col,u' {}'.format(d) )
		
		# Fix up the column and row sizes.
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )
		
	def refresh( self ):
		model = Model.model
		riders = model.riders
		
		self.renumberButton.Show( model.competition.isMTB )
		
		Utils.AdjustGridSize( self.grid, rowsRequired = len(riders) )
		for row, r in enumerate(riders):
			for col, value in enumerate([u'{}'.format(r.bib), r.full_name, r.team, r.qualifyingTimeText]):
				self.grid.SetCellValue( row, col, value )
				
		# Fix up the column and row sizes.
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )
		self.grid.SetColSize( self.grid.GetNumberCols()-1, 96 )
		
		self.Layout()
		self.Refresh()
		
	def setQT( self ):
		# The qualifying times can be changed at any time, however, if the competition is under way, the events cannot
		# be adjusted.
		model = Model.model
		riders = model.riders
		
		self.grid.SaveEditControlValue()

		for row in six.moves.range(self.grid.GetNumberRows()):
			v = self.grid.GetCellValue( row, self.iTime ).strip()
			if v:
				qt = Utils.StrToSeconds( v )
			else:
				qt = Model.QualifyingTimeDefault
				
			qt = min( qt, Model.QualifyingTimeDefault )
			status = self.grid.GetCellValue( row, self.iStatus ).strip()
			
			rider = riders[row]
			if rider.qualifyingTime != qt or rider.status != status:
				rider.qualifyingTime = qt
				rider.status = status
				model.setChanged( True )
		
	def commit( self ):
		# The qualifying times can be changed at any time, however, if the competition is underway, the events cannot
		# be adusted.
		model = Model.model
		riders = model.riders
		self.setQT()
		if model.canReassignStarters():
			model.setQualifyingTimes()
			Utils.getMainWin().resetEvents()
			
	def doRenumber( self, event ):
		if not Utils.MessageOKCancel( self, 'Sequence Bib numbers in Increasing Order by Qualifying Time.\n\nContinue?', 'Renumber Riders' ):
			return
	
		self.setQT()
		
		model = Model.model
		riders = sorted( model.riders, key = lambda x: x.keyQualifying() )
		for r, rider in enumerate(riders, 1):
			rider.bib = r
		
		wx.CallAfter( self.refresh )
		
########################################################################

class QualifiersFrame(wx.Frame):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		wx.Frame.__init__(self, None, title="Qualifier Grid Test", size=(800,600) )
		panel = Qualifiers(self)
		panel.refresh()
		self.Show()
 
#----------------------------------------------------------------------
if __name__ == "__main__":
	Model.model = SetDefaultData()
	app = wx.App(False)
	frame = QualifiersFrame()
	app.MainLoop()
