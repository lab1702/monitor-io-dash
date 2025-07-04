"""Constants for Monitor IO Dashboard"""
from matplotlib.dates import DateFormatter, HourLocator, DayLocator

# Performance constants
DEFAULT_TIME_RANGE_DAYS = 1
MAX_TIME_RANGE_DAYS = 365

# Time range dropdown options
TIME_RANGE_OPTIONS = {
    "Last 24 hours": 1,
    "Last 48 hours": 2,
    "Last 7 days": 7,
    "All Data": None
}

DEFAULT_TIME_RANGE_SELECTION = "Last 24 hours"

# Chart formatting constants
# VSCode-style chart colors for light theme
CHART_COLORS_LIGHT = [
    '#005fb8',  # VSCode blue
    '#16825d',  # VSCode green
    '#b75502',  # VSCode orange
    '#d73a49',  # VSCode red
    '#8250df',  # VSCode purple
    '#0969da'   # VSCode info blue
]

# VSCode-style chart colors for dark theme
CHART_COLORS_DARK = [
    '#007acc',  # VSCode dark blue
    '#4ec9b0',  # VSCode dark green
    '#ffcc02',  # VSCode dark yellow
    '#f44747',  # VSCode dark red
    '#c586c0',  # VSCode dark purple
    '#75beff'   # VSCode dark light blue
]

# For backward compatibility
CHART_COLORS = CHART_COLORS_DARK

CHART_LINE_WIDTH = 2
CHART_ALPHA = 0.8

# Time formatting intervals
TIME_RANGE_INTERVALS = {
    1: {'locator': HourLocator(interval=4), 'formatter': DateFormatter('%m/%d %H:%M')},
    2: {'locator': HourLocator(interval=6), 'formatter': DateFormatter('%m/%d %H:%M')},
    7: {'locator': HourLocator(interval=12), 'formatter': DateFormatter('%m/%d %H:%M')},
    30: {'locator': DayLocator(interval=1), 'formatter': DateFormatter('%m/%d')},
    365: {'locator': DayLocator(interval=7), 'formatter': DateFormatter('%m/%d')}
}

# UI Constants (kept for backward compatibility)
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