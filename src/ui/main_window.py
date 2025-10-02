"""
Main window for PneumoStabSim application
"""
from PySide6.QtWidgets import QMainWindow, QStatusBar, QDockWidget, QWidget
from PySide6.QtCore import Qt
from .gl_view import GLView
from .charts import ChartWidget


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PneumoStabSim - Pneumatic Stabilizer Simulator")
        self.setGeometry(100, 100, 1200, 800)
        
        # Setup central OpenGL widget
        self.gl_view = GLView()
        self.setCentralWidget(self.gl_view)
        
        # Setup status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Setup dock widget with charts
        self.chart_dock = QDockWidget("Charts", self)
        self.chart_widget = ChartWidget()
        self.chart_dock.setWidget(self.chart_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.chart_dock)
        
        # Set dock widget properties
        self.chart_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )