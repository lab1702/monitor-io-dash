"""UI Components for Monitor IO Dashboard"""
from shiny import ui
from constants import METRIC_TYPES, DEFAULT_SLIDER_MIN, DEFAULT_SLIDER_MAX, DEFAULT_TIME_RANGE_DAYS

def create_header():
    """Create the dashboard header section"""
    return ui.div(
        ui.div(
            ui.h1("🌐 Monitor IO Dashboard", class_="dashboard-title"),
            class_="header-container"
        ),
        class_="mb-4"
    )

def create_control_panel():
    """Create the control panel with metric selector and time range"""
    return ui.div(
        # Controls Row
        ui.row(
            ui.column(
                6,
                ui.div(
                    ui.input_selectize(
                        "metric_type",
                        "📊 Metric Type",
                        choices=list(METRIC_TYPES.values()),
                        selected=METRIC_TYPES['AVERAGE_PING']
                    ),
                    class_="control-group"
                )
            ),
            ui.column(
                6,
                ui.div(
                    ui.input_slider("time_range", "📅 Days", DEFAULT_SLIDER_MIN, DEFAULT_SLIDER_MAX, DEFAULT_TIME_RANGE_DAYS),
                    class_="control-group",
                    style="display: flex; flex-direction: column; align-items: flex-end;"
                )
            )
        ),
        # Status Row
        ui.row(
            ui.column(
                12,
                ui.div(
                    ui.output_ui("loading_status"),
                    ui.div(
                        ui.output_text("data_status"),
                        class_="status-display"
                    ),
                    class_="status-container"
                )
            )
        ),
        class_="control-panel"
    )

def create_chart_section():
    """Create the chart visualization section"""
    return ui.div(
        ui.div(
            ui.h4("📊 Network Performance & DNS Failure Events", class_="chart-title"),
            ui.output_plot("metric_plot"),
            class_="chart-content"
        ),
        class_="chart-container"
    )

def create_data_tables():
    """Create the data tables section"""
    return ui.row(
        ui.column(
            6,
            ui.div(
                ui.div(
                    ui.h5("🕒 Recent Measurements", class_="table-title"),
                    ui.output_table("recent_data_table"),
                    class_="table-content"
                ),
                class_="table-container"
            )
        ),
        ui.column(
            6,
            ui.div(
                ui.div(
                    ui.h5("📈 Performance Statistics", class_="table-title"),
                    ui.output_table("stats_table"),
                    class_="table-content"
                ),
                class_="table-container"
            )
        )
    )

def get_dashboard_styles():
    """Get the CSS styles for the dashboard"""
    import os
    css_path = os.path.join(os.path.dirname(__file__), 'static', 'styles.css')
    try:
        with open(css_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        # Fallback to minimal styling if CSS file not found
        return """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .dashboard-title { font-size: 2rem; font-weight: bold; text-align: center; }
        """

def create_main_layout():
    """Create the main application layout"""
    return ui.page_fluid(
        # Include CSS styles
        ui.tags.head(
            ui.tags.style(get_dashboard_styles())
        ),
        
        # Header Section
        create_header(),
        
        # Main Content Container
        ui.div(
            # Top Row - Controls and Status
            ui.row(
                ui.column(12, create_control_panel())
            ),
            
            # Chart Section
            ui.row(
                ui.column(12, create_chart_section())
            ),
            
            # Data Tables Section
            create_data_tables(),
            
            class_="main-container"
        )
    )