"""Configuration management for Monitor IO Dashboard"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

@dataclass
class AppConfig:
    """Application configuration settings"""
    # Monitor IO device settings
    monitor_io_url: str = os.environ.get('MONITOR_IO_URL', 'http://192.168.0.246/')
    request_timeout: int = int(os.environ.get('REQUEST_TIMEOUT', '10'))
    
    # Application settings
    app_host: str = os.environ.get('APP_HOST', '0.0.0.0')
    app_port: int = int(os.environ.get('APP_PORT', '8000'))
    
    # Performance settings
    concurrent_downloads: int = int(os.environ.get('CONCURRENT_DOWNLOADS', '5'))
    
    # Logging settings
    log_level: str = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Security settings
    use_https: bool = os.environ.get('USE_HTTPS', 'false').lower() == 'true'
    ssl_cert_path: Optional[str] = os.environ.get('SSL_CERT_PATH')
    ssl_key_path: Optional[str] = os.environ.get('SSL_KEY_PATH')
    
    # File exclusion settings
    excluded_files: list = None
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        # Initialize excluded files list
        if self.excluded_files is None:
            excluded_str = os.environ.get('EXCLUDED_FILES', 'Latest_NetMonitor_Results.log,NetMonitor_Event_Summary.csv')
            self.excluded_files = [f.strip() for f in excluded_str.split(',') if f.strip()]
        
        # Ensure URL has trailing slash
        if not self.monitor_io_url.endswith('/'):
            self.monitor_io_url += '/'
        
        # Validate timeout
        if self.request_timeout <= 0:
            raise ValueError("REQUEST_TIMEOUT must be positive")
        
        # Validate port
        if not (1 <= self.app_port <= 65535):
            raise ValueError("APP_PORT must be between 1 and 65535")
        
        # Validate concurrent downloads
        if self.concurrent_downloads <= 0:
            raise ValueError("CONCURRENT_DOWNLOADS must be positive")
        
        
        # Validate HTTPS settings
        if self.use_https:
            if not self.ssl_cert_path or not self.ssl_key_path:
                raise ValueError("SSL_CERT_PATH and SSL_KEY_PATH must be set when USE_HTTPS is true")
            
            if not os.path.exists(self.ssl_cert_path):
                raise ValueError(f"SSL certificate file not found: {self.ssl_cert_path}")
            
            if not os.path.exists(self.ssl_key_path):
                raise ValueError(f"SSL key file not found: {self.ssl_key_path}")

# Global configuration instance
config = AppConfig()