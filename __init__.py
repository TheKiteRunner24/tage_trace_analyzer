# __init__.py
"""
PC Misprediction Analyzer - Analyze branch prediction mispredictions from CondTrace tables

This package provides tools to analyze PC misprediction statistics from CondTrace tables,
generate visualizations, and provide a web interface for interactive analysis.
"""

__version__ = "1.0.0"
__author__ = "PC Misprediction Analyzer"

from .analyzer import analyze_mispredictions, print_results, export_to_csv
from .visualizer import create_static_chart, create_export_chart
from .web_app import MispredictionWebApp