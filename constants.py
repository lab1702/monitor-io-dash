"""Constants for Monitor IO Dashboard"""
from matplotlib.dates import DateFormatter, HourLocator, DayLocator

# Performance constants
DEFAULT_TIME_RANGE_DAYS = 1
MAX_TIME_RANGE_DAYS = 365

# Chart formatting constants
CHART_COLORS = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0891b2']
CHART_LINE_WIDTH = 2
CHART_ALPHA = 0.8

# Time formatting intervals
TIME_RANGE_INTERVALS = {
    1: {'locator': HourLocator(interval=4), 'formatter': DateFormatter('%m/%d %H:%M')},
    7: {'locator': HourLocator(interval=12), 'formatter': DateFormatter('%m/%d %H:%M')},
    30: {'locator': DayLocator(interval=1), 'formatter': DateFormatter('%m/%d')},
    365: {'locator': DayLocator(interval=7), 'formatter': DateFormatter('%m/%d')}
}

# UI Constants
DEFAULT_SLIDER_MIN = 1
DEFAULT_SLIDER_MAX = 30
RECENT_DATA_ROWS = 15

# Data processing constants
DNS_FAILURE_PREFIX = 'DNS:Failure'

# Metric types
METRIC_TYPES = {
    'AVERAGE_PING': 'Average Ping Time',
    'MIN_PING': 'Min Ping Time', 
    'MAX_PING': 'Max Ping Time',
    'PACKET_LOSS': 'Packet Loss'
}

# Column names
PING_COLUMNS = {
    'delay_avg': 'delay_avg',
    'delay_min': 'delay_min', 
    'delay_max': 'delay_max',
    'loss_pct': 'loss_pct'
}