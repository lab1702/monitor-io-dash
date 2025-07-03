# Monitor IO Dashboard

A professional Python/Shiny web dashboard for monitoring network performance data from monitor-io devices. Features real-time data visualization, concurrent data processing, and responsive design with dark/light mode support.

## Features

- 🌐 **Real-time Network Monitoring**: Visualize ping times and packet loss across multiple targets
- 📊 **Multiple Metrics**: Average/Min/Max ping times and packet loss percentages
- ⏰ **Flexible Time Ranges**: View data from 1-365 days with smart downsampling
- 🚀 **High Performance**: Concurrent data downloads and vectorized processing for 1M+ data points
- 📱 **Responsive Design**: Professional UI with automatic dark/light mode support
- 🔧 **Configurable**: Environment-based configuration for easy deployment
- 🐳 **Docker Ready**: Complete containerization with security best practices

## Quick Start

### Using Docker (Recommended)

1. **Clone and configure**:
   ```bash
   git clone <repository-url>
   cd monitor-io-dash
   cp .env.example .env
   # Edit .env with your monitor-io device URL
   ```

2. **Run with Docker**:
   ```bash
   docker compose up --build
   ```

3. **Access dashboard**: Open http://localhost:8000

### Manual Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run application**:
   ```bash
   python app.py
   ```

## Configuration

All configuration is managed through environment variables. Copy `.env.example` to `.env` and customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONITOR_IO_URL` | `http://192.168.0.246/` | URL of your monitor-io device |
| `APP_HOST` | `0.0.0.0` | Host to bind the application |
| `APP_PORT` | `8000` | Port to run the application |
| `REQUEST_TIMEOUT` | `10` | HTTP request timeout in seconds |
| `CONCURRENT_DOWNLOADS` | `5` | Number of concurrent CSV downloads |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `USE_HTTPS` | `false` | Enable HTTPS (requires SSL certificates) |
| `EXCLUDED_FILES` | `Latest_NetMonitor_Results.log,NetMonitor_Event_Summary.csv` | Files to exclude from processing |

## Architecture

- **`app.py`**: Main Shiny application with UI and server logic
- **`data_fetcher.py`**: Async data fetching and processing with error handling
- **`config.py`**: Centralized configuration management with validation
- **`constants.py`**: Application constants and configuration values
- **`exceptions.py`**: Custom exception classes for better error handling
- **`ui_components.py`**: Modular UI component definitions
- **`static/styles.css`**: Professional CSS styling with dark/light mode

## Data Processing

The dashboard processes CSV files from monitor-io devices with:

- **Concurrent Downloads**: Batched async downloads for improved performance
- **Data Validation**: Input validation and error handling for malformed data
- **Smart Filtering**: Automatic exclusion of DNS failures and invalid targets
- **Vectorized Processing**: Pandas-optimized data restructuring
- **Intelligent Downsampling**: Automatic data reduction for smooth chart rendering

## Development

### Running Tests

```bash
# Examine data structure
python scripts/examine_data.py

# Check configuration
python -c "from config import config; print(config)"
```

### Adding Features

1. **New Metrics**: Add to `constants.py` METRIC_TYPES
2. **UI Components**: Extend `ui_components.py`
3. **Data Processing**: Modify `data_fetcher.py`
4. **Configuration**: Update `config.py` and `.env.example`

## Production Deployment

### Docker with HTTPS

1. **Obtain SSL certificates**
2. **Configure environment**:
   ```bash
   USE_HTTPS=true
   SSL_CERT_PATH=/path/to/cert.pem
   SSL_KEY_PATH=/path/to/key.pem
   ```
3. **Deploy with certificates mounted**

### Security Considerations

- Non-root user in Docker container
- Input validation and sanitization
- Environment-based configuration
- Optional HTTPS support
- Request timeout and rate limiting

## Performance

- **Concurrent Processing**: 5x faster data loading
- **Memory Efficient**: Vectorized operations for large datasets
- **Smart Downsampling**: Handles 1M+ data points smoothly
- **Responsive UI**: Optimized for real-time updates

## License

[Add your license information here]

## Support

For issues and questions:
- Check the logs: `docker compose logs`
- Review configuration: Ensure `.env` settings are correct
- Verify network access: Confirm monitor-io device is accessible

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

---

Built with Python, Shiny, pandas, matplotlib, aiohttp, and Docker.