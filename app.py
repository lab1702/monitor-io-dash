from shiny import App, ui, render, reactive
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter, HourLocator, DayLocator
from datetime import datetime, timedelta
import logging
import asyncio
import warnings
from typing import Optional, List, Dict, Any

from data_fetcher import MonitorIODataFetcher
from config import config
from constants import *
from exceptions import DataProcessingError, ValidationError
from ui_components import create_main_layout

logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)

# Suppress specific matplotlib tight_layout warning
warnings.filterwarnings('ignore', message='This figure includes Axes that are not compatible with tight_layout')

# Create UI using modular components
app_ui = create_main_layout()

def _plot_metric(ax, filtered_data: pd.DataFrame, targets: List[str], colors: List[str], 
                column: str, ylabel: str) -> None:
    """Helper function to plot a specific metric for all targets"""
    for i, target in enumerate(targets):
        target_data = filtered_data[filtered_data['target'] == target]
        if not target_data.empty and target_data[column].notna().any():
            clean_data = target_data.dropna(subset=[column])
            if not clean_data.empty:
                ax.plot(clean_data['datetime'], clean_data[column],
                       label=str(target), color=colors[i % len(colors)],
                       linewidth=CHART_LINE_WIDTH, alpha=CHART_ALPHA)
    
    ax.set_ylabel(ylabel, fontweight='bold', fontsize=12)

def server(input, output, session):
    # Initialize data fetcher
    fetcher = MonitorIODataFetcher()
    
    # Reactive values to store the data
    ping_data = reactive.Value(pd.DataFrame())
    dns_failure_data = reactive.Value(pd.DataFrame())
    target_choices = reactive.Value([])
    
    # Load initial data
    @reactive.Effect
    async def load_initial_data():
        with ui.Progress(min=0, max=100) as p:
            try:
                p.set(0, message="Connecting to monitor-io device...", detail="")
                await asyncio.sleep(0.1)
                
                # Progress callback function
                async def update_progress(progress, message):
                    p.set(progress, message=message, detail="")
                    await asyncio.sleep(0.05)  # Allow UI to update
                
                # Use async method with progress callback
                data = await fetcher.get_ping_data_async(progress_callback=update_progress)
                
                p.set(90, message="Loading DNS failure data...", detail="")
                dns_data = await fetcher.get_dns_failure_data_async()
                
                p.set(98, message="Finalizing...", detail="Updating interface")
                ping_data.set(data)
                dns_failure_data.set(dns_data)
                
                # Update target choices
                if not data.empty and 'target' in data.columns:
                    unique_targets = data['target'].dropna().unique().tolist()
                    target_choices.set(unique_targets)
                
                p.set(100, message="Complete!", detail=f"Loaded {len(data)} records")
                await asyncio.sleep(0.5)  # Brief pause to show completion
                
                logger.info(f"Loaded initial data: {len(data)} rows")
            except Exception as e:
                p.set(100, message="Error loading data", detail=str(e))
                logger.error(f"Error loading initial data: {e}")
                ping_data.set(pd.DataFrame())
                target_choices.set([])
                await asyncio.sleep(1)
    
    
    # Helper function to get time range in days from dropdown selection
    def get_time_range_days():
        try:
            selection = input.time_range()
            logger.info(f"Time range selection: '{selection}'")
            if selection in TIME_RANGE_OPTIONS:
                days = TIME_RANGE_OPTIONS[selection]
                logger.info(f"Mapped to {days} days")
                if days is None:  # "All Data" option
                    return None
                return days
            logger.warning(f"Unknown selection '{selection}', using default")
            return 1  # Default fallback
        except Exception as e:
            logger.error(f"Error getting time range: {e}")
            return 1
    
    @output
    @render.plot
    def metric_plot():
        logger.info("=== METRIC PLOT FUNCTION CALLED ===")
        data = ping_data.get()
        dns_data = dns_failure_data.get()
        
        # Set up matplotlib with subplots - performance chart on top, DNS failures on bottom
        plt.style.use('default')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, 
                                       gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.1},
                                       constrained_layout=False)
        
        # Configure for transparent background to work with CSS themes
        fig.patch.set_facecolor('none')
        ax1.set_facecolor('none')
        ax2.set_facecolor('none')
        
        # VSCode theme colors for charts
        text_color = '#cccccc'  # VSCode dark text
        muted_color = '#969696'  # VSCode muted text
        border_color = '#464647'  # VSCode border
        
        # Get time range for consistent filtering
        logger.info("=== STARTING TIME RANGE CALCULATION ===")
        time_range_days = get_time_range_days()
        current_time = datetime.now()
        logger.info(f"Calculated time_range_days: {time_range_days}, current_time: {current_time}")
        
        if time_range_days is None:  # "All Data" option
            cutoff_time = None
        else:
            cutoff_time = current_time - timedelta(days=time_range_days)
        
        # === TOP SUBPLOT: Performance Metrics ===
        if data.empty or 'datetime' not in data.columns:
            ax1.text(0.5, 0.5, 'No performance data available\nClick "🔄 Refresh Data" to load from monitor-io device',
                    ha='center', va='center', transform=ax1.transAxes, fontsize=12, color=muted_color)
        else:
            # Filter performance data by time range
            try:
                if not pd.api.types.is_datetime64_any_dtype(data['datetime']):
                    data['datetime'] = pd.to_datetime(data['datetime'])
                    
                if cutoff_time is None:  # "All Data" option
                    filtered_data = data.copy()
                    logger.info(f"No filtering - showing all {len(filtered_data)} records")
                else:
                    filtered_data = data[data['datetime'] >= cutoff_time].copy()
                    logger.info(f"Filtered data: {len(data)} -> {len(filtered_data)} records "
                               f"(cutoff: {cutoff_time}, latest: {data['datetime'].max()}, "
                               f"oldest: {data['datetime'].min()})")
            except Exception as e:
                filtered_data = data.copy()
                logger.error(f"Error filtering data: {e}")
            
            if filtered_data.empty:
                ax1.text(0.5, 0.5, 'No performance data in selected time range',
                        ha='center', va='center', transform=ax1.transAxes, fontsize=12, color=muted_color)
            else:
                # Use VSCode dark theme color palette for charts
                colors = CHART_COLORS_DARK
                targets = filtered_data['target'].unique()
                metric_type = input.metric_type()
                
                if metric_type == METRIC_TYPES['AVERAGE_PING']:
                    _plot_metric(ax1, filtered_data, targets, colors, PING_COLUMNS['delay_avg'], 
                                'Average Ping Time (ms)')
                elif metric_type == METRIC_TYPES['MIN_PING']:
                    _plot_metric(ax1, filtered_data, targets, colors, PING_COLUMNS['delay_min'], 
                                'Min Ping Time (ms)')
                elif metric_type == METRIC_TYPES['MAX_PING']:
                    _plot_metric(ax1, filtered_data, targets, colors, PING_COLUMNS['delay_max'], 
                                'Max Ping Time (ms)')
                elif metric_type == METRIC_TYPES['PACKET_LOSS']:
                    _plot_metric(ax1, filtered_data, targets, colors, PING_COLUMNS['loss_pct'], 
                                'Packet Loss (%)')
                
                # Style the axes for dark mode
                ax1.tick_params(colors=text_color, labelsize=10)
                ax1.yaxis.label.set_color(text_color)
                
                # Add legend if we have data
                if len(targets) > 0:
                    legend1 = ax1.legend(loc='upper left', fontsize=9)
                    legend1.get_frame().set_facecolor('none')
                    legend1.get_frame().set_alpha(0)
                    # Make legend text light colored
                    for text in legend1.get_texts():
                        text.set_color(text_color)
        
        # === BOTTOM SUBPLOT: DNS Failures ===
        if dns_data.empty:
            ax2.text(0.5, 0.5, 'No DNS failures detected',
                    ha='center', va='center', transform=ax2.transAxes, fontsize=10, color=muted_color)
            ax2.set_ylim(-0.5, 0.5)  # Minimal range when no data
            ax2.set_yticks([])  # No tick marks when no data
            ax2.tick_params(colors=text_color, labelsize=10)
        else:
            # Filter DNS failure data by time range
            try:
                if 'datetime' in dns_data.columns:
                    if not pd.api.types.is_datetime64_any_dtype(dns_data['datetime']):
                        dns_data['datetime'] = pd.to_datetime(dns_data['datetime'])
                    
                    if cutoff_time is None:  # "All Data" option
                        filtered_dns_data = dns_data.copy()
                    else:
                        filtered_dns_data = dns_data[dns_data['datetime'] >= cutoff_time].copy()
                else:
                    filtered_dns_data = dns_data.copy()
            except:
                filtered_dns_data = dns_data.copy()
            
            if filtered_dns_data.empty:
                ax2.text(0.5, 0.5, 'No DNS failures in selected time range',
                        ha='center', va='center', transform=ax2.transAxes, fontsize=10, color=muted_color)
                ax2.set_ylim(-0.5, 0.5)  # Minimal range when no data
                ax2.set_yticks([])  # No tick marks when no data
                ax2.tick_params(colors=text_color, labelsize=10)
            else:
                # Plot DNS failures as vertical lines
                target_numbers = filtered_dns_data['target_number'].unique()
                colors = CHART_COLORS_DARK
                
                # Set up Y-axis range for vertical lines
                ax2.set_ylim(-0.5, 0.5)
                ax2.set_yticks([])  # No target number ticks needed for vertical lines
                
                for i, target_num in enumerate(sorted(target_numbers)):
                    target_data = filtered_dns_data[filtered_dns_data['target_number'] == target_num]
                    if not target_data.empty:
                        for _, failure in target_data.iterrows():
                            ax2.axvline(x=failure['datetime'], 
                                       color=colors[i % len(colors)], alpha=0.8, linewidth=2,
                                       label=f'Target {target_num}' if _ == target_data.index[0] else "")
                
                # Add legend if there are multiple targets
                if len(target_numbers) > 1:
                    legend2 = ax2.legend(loc='upper right', fontsize=8)
                    legend2.get_frame().set_facecolor('none')
                    legend2.get_frame().set_alpha(0)
                    # Make legend text light colored
                    for text in legend2.get_texts():
                        text.set_color(text_color)
        
        ax2.set_ylabel('DNS', fontweight='bold', fontsize=10, color=text_color)
        
        # Style ax2 for dark mode
        ax2.tick_params(colors=text_color, labelsize=10)
        ax2.yaxis.label.set_color(text_color)
        
        # === SHARED X-AXIS FORMATTING ===
        # Set explicit X-axis range for both subplots
        if cutoff_time is not None:
            ax1.set_xlim(cutoff_time, current_time)
            ax2.set_xlim(cutoff_time, current_time)
        
        # Format time axis (only on bottom subplot since sharex=True)
        if time_range_days is not None:
            interval_key = 1  # default
            for key in sorted(TIME_RANGE_INTERVALS.keys()):
                if time_range_days <= key:
                    interval_key = key
                    break
            else:
                interval_key = max(TIME_RANGE_INTERVALS.keys())
        else:
            # For "All Data", use the largest interval
            interval_key = max(TIME_RANGE_INTERVALS.keys())
        
        interval_config = TIME_RANGE_INTERVALS[interval_key]
        ax2.xaxis.set_major_locator(interval_config['locator'])
        ax2.xaxis.set_major_formatter(interval_config['formatter'])
        
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right', color=text_color)
        ax2.set_xlabel('Time', fontweight='bold', fontsize=12, color=text_color)
        ax2.xaxis.label.set_color(text_color)
        
        plt.subplots_adjust(bottom=0.15, hspace=0.1)
        fig.set_tight_layout(False)
        logger.info(f"Generated combined chart: performance data and DNS failures")
        return fig
    
    @output
    @render.table
    def stats_table():
        data = ping_data.get()
        if data.empty:
            return pd.DataFrame({"Target": ["No data"], "Avg Ping (ms)": ["N/A"], "Min Ping (ms)": ["N/A"], "Max Ping (ms)": ["N/A"], "Avg Loss (%)": ["N/A"], "Records": ["N/A"]})
        
        # Apply time range filtering (same logic as chart)
        time_range_days = get_time_range_days()
        current_time = datetime.now()
        
        if time_range_days is None:  # "All Data" option
            cutoff_time = None
        else:
            cutoff_time = current_time - timedelta(days=time_range_days)
        
        # Filter data by time range
        try:
            if 'datetime' in data.columns:
                if not pd.api.types.is_datetime64_any_dtype(data['datetime']):
                    data['datetime'] = pd.to_datetime(data['datetime'])
                
                if cutoff_time is None:  # "All Data" option
                    filtered_data = data.copy()
                else:
                    filtered_data = data[data['datetime'] >= cutoff_time].copy()
            else:
                filtered_data = data.copy()
        except Exception as e:
            logger.error(f"Error filtering stats data: {e}")
            filtered_data = data.copy()
        
        if filtered_data.empty:
            return pd.DataFrame({"Target": ["No data in selected time range"], "Avg Ping (ms)": ["N/A"], "Min Ping (ms)": ["N/A"], "Max Ping (ms)": ["N/A"], "Avg Loss (%)": ["N/A"], "Records": ["N/A"]})
        
        stats = []
        
        # Statistics by target - now as rows
        for target in sorted(filtered_data['target'].unique()):
            target_data = filtered_data[filtered_data['target'] == target]
            
            if not target_data.empty:
                # Calculate average loss and handle potential NaN/null values
                avg_loss = target_data['loss_pct'].mean()
                
                # Handle NaN values and ensure we have a valid number
                if pd.isna(avg_loss):
                    avg_loss = 0.0
                else:
                    avg_loss = float(avg_loss)
                
                # Add warning emoji for targets with packet loss (only in loss column)
                target_display = target
                loss_display = f"{avg_loss:.1f}"
                
                # Check for packet loss (use more precise threshold to handle floating point precision)
                if avg_loss > 0.01:  # Greater than 0.01% to avoid floating point precision issues
                    loss_display = f"⚠️ {avg_loss:.1f}"
                
                stats.append({
                    "Target": target_display,
                    "Avg Ping (ms)": f"{target_data['delay_avg'].mean():.1f}",
                    "Min Ping (ms)": f"{target_data['delay_min'].min():.1f}",
                    "Max Ping (ms)": f"{target_data['delay_max'].max():.1f}",
                    "Avg Loss (%)": loss_display,
                    "Records": str(len(target_data))
                })
        
        return pd.DataFrame(stats)
    
    @output
    @render.ui
    def loading_status():
        # Progress bars are now handled by ui.Progress context manager
        return ui.div()  # Empty - progress is shown via ui.Progress
    
    @output
    @render.text
    def data_status():
        data = ping_data.get()
        targets = target_choices.get()
        
        if data.empty:
            return "Status: No data loaded"
        
        total_targets = len(targets)
        
        return f"Status: {len(data)} records loaded\nTargets: {total_targets} available\nTime range: {input.time_range()} days"

app = App(app_ui, server)

if __name__ == "__main__":
    if config.use_https and config.ssl_cert_path and config.ssl_key_path:
        app.run(host=config.app_host, port=config.app_port, 
                ssl_certfile=config.ssl_cert_path, ssl_keyfile=config.ssl_key_path)
    else:
        app.run(host=config.app_host, port=config.app_port)
