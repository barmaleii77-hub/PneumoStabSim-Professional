"""
Charts widget using QtCharts
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCharts import QChart, QChartView, QLineSeries
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter


class ChartWidget(QWidget):
    """Widget containing QtCharts for data visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create empty chart
        self.chart = QChart()
        self.chart.setTitle("Pneumatic System Data")
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # Create empty line series
        self.series = QLineSeries()
        self.series.setName("Sample Data")
        self.chart.addSeries(self.series)
        
        # Create axes
        self.chart.createDefaultAxes()
        
        # Create chart view
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Add to layout
        layout.addWidget(self.chart_view)
        
    def add_data_point(self, x, y):
        """Add a data point to the chart"""
        self.series.append(x, y)