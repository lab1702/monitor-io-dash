import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import io
import logging
import asyncio
from typing import List, Dict, Optional, Callable
from urllib.parse import urlparse, urljoin
import aiohttp
import time

from config import config
from constants import DNS_FAILURE_PREFIX
from exceptions import DataFetchError, DataProcessingError, ValidationError, ConnectionError

logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)

class MonitorIODataFetcher:
    def __init__(self, base_url: Optional[str] = None):
        """Initialize data fetcher with optional base URL override"""
        self.base_url = base_url or config.monitor_io_url
        self._validate_base_url()
        
        self.session = requests.Session()
        self.session.timeout = config.request_timeout
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'failed_requests': 0,
            'total_download_time': 0,
            'last_fetch_time': None
        }
    
    def _validate_base_url(self) -> None:
        """Validate base URL format and accessibility"""
        if not self.base_url:
            raise ValidationError("Base URL cannot be empty")
        
        parsed = urlparse(self.base_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValidationError(f"Invalid URL format: {self.base_url}")
        
        # Ensure trailing slash
        if not self.base_url.endswith('/'):
            self.base_url += '/'
    
    def _validate_csv_url(self, url: str) -> bool:
        """Validate CSV URL is safe to access"""
        try:
            # Ensure URL is from expected domain
            if not url.startswith(self.base_url):
                logger.warning(f"URL not from expected domain: {url}")
                return False
            
            # Check file extension
            if not url.endswith('.csv'):
                logger.warning(f"URL is not a CSV file: {url}")
                return False
            
            # Check against excluded files
            filename = url.split('/')[-1]
            if filename in config.excluded_files:
                logger.info(f"Skipping excluded file: {filename}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating URL {url}: {e}")
            return False
    
    def get_csv_links(self) -> List[str]:
        """Fetch all CSV file links from the monitor-io device"""
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            csv_links = []
            
            # Look for links ending with .csv
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Convert relative URLs to absolute
                if not href.startswith('http'):
                    href = urljoin(self.base_url, href)
                
                # Validate the URL
                if self._validate_csv_url(href):
                    csv_links.append(href)
            
            self.stats['total_download_time'] += time.time() - start_time
            logger.info(f"Found {len(csv_links)} valid CSV files")
            return csv_links
            
        except requests.ConnectionError as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Connection error accessing {self.base_url}: {e}")
            raise ConnectionError(f"Cannot connect to monitor-io device at {self.base_url}")
        except requests.Timeout as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Timeout accessing {self.base_url}: {e}")
            raise DataFetchError(f"Request timeout accessing {self.base_url}")
        except requests.HTTPError as e:
            self.stats['failed_requests'] += 1
            logger.error(f"HTTP error {e.response.status_code} accessing {self.base_url}: {e}")
            raise DataFetchError(f"HTTP error {e.response.status_code} accessing {self.base_url}")
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Unexpected error fetching CSV links: {e}")
            raise DataFetchError(f"Failed to fetch CSV links: {str(e)}")
    
    def download_csv(self, csv_url: str) -> Optional[pd.DataFrame]:
        """Download and parse a single CSV file"""
        if not self._validate_csv_url(csv_url):
            return None
        
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            response = self.session.get(csv_url)
            response.raise_for_status()
            
            # Validate content type
            content_type = response.headers.get('content-type', '')
            if 'text/csv' not in content_type and 'text/plain' not in content_type:
                logger.warning(f"Unexpected content type for {csv_url}: {content_type}")
            
            # Parse CSV with flexible column handling
            csv_data = io.StringIO(response.text)
            df = pd.read_csv(csv_data)
            
            # Validate DataFrame
            if df.empty:
                logger.warning(f"Empty CSV file: {csv_url}")
                return None
            
            # Add source file info
            df['source_file'] = csv_url.split('/')[-1]
            
            self.stats['total_download_time'] += time.time() - start_time
            logger.info(f"Downloaded {csv_url}: {len(df)} rows, columns: {list(df.columns)}")
            return df
            
        except requests.ConnectionError as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Connection error downloading {csv_url}: {e}")
            return None
        except requests.Timeout as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Timeout downloading {csv_url}: {e}")
            return None
        except requests.HTTPError as e:
            self.stats['failed_requests'] += 1
            logger.error(f"HTTP error {e.response.status_code} downloading {csv_url}: {e}")
            return None
        except pd.errors.EmptyDataError:
            logger.warning(f"Empty CSV file: {csv_url}")
            return None
        except pd.errors.ParserError as e:
            logger.error(f"CSV parsing error for {csv_url}: {e}")
            return None
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Unexpected error downloading {csv_url}: {e}")
            return None
    
    async def download_csv_async(self, session: aiohttp.ClientSession, csv_url: str) -> Optional[pd.DataFrame]:
        """Async download and parse a single CSV file"""
        if not self._validate_csv_url(csv_url):
            return None
        
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            async with session.get(csv_url) as response:
                response.raise_for_status()
                
                # Validate content type
                content_type = response.headers.get('content-type', '')
                if 'text/csv' not in content_type and 'text/plain' not in content_type:
                    logger.warning(f"Unexpected content type for {csv_url}: {content_type}")
                
                # Read and parse CSV
                content = await response.text()
                csv_data = io.StringIO(content)
                df = pd.read_csv(csv_data)
                
                # Validate DataFrame
                if df.empty:
                    logger.warning(f"Empty CSV file: {csv_url}")
                    return None
                
                # Add source file info
                df['source_file'] = csv_url.split('/')[-1]
                
                self.stats['total_download_time'] += time.time() - start_time
                logger.info(f"Downloaded {csv_url}: {len(df)} rows, columns: {list(df.columns)}")
                return df
                
        except aiohttp.ClientConnectionError as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Connection error downloading {csv_url}: {e}")
            return None
        except aiohttp.ServerTimeoutError as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Timeout downloading {csv_url}: {e}")
            return None
        except aiohttp.ClientResponseError as e:
            self.stats['failed_requests'] += 1
            logger.error(f"HTTP error {e.status} downloading {csv_url}: {e}")
            return None
        except pd.errors.EmptyDataError:
            logger.warning(f"Empty CSV file: {csv_url}")
            return None
        except pd.errors.ParserError as e:
            logger.error(f"CSV parsing error for {csv_url}: {e}")
            return None
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Unexpected error downloading {csv_url}: {e}")
            return None
    
    async def fetch_all_data_async(self, progress_callback: Optional[Callable] = None) -> pd.DataFrame:
        """Fetch all CSV data concurrently and combine into single DataFrame with progress updates"""
        start_time = time.time()
        self.stats['last_fetch_time'] = datetime.now()
        
        try:
            csv_links = self.get_csv_links()
            all_data = []
            
            if not csv_links:
                logger.warning("No CSV files found")
                return pd.DataFrame()
            
            if progress_callback:
                await progress_callback(10, f"Found {len(csv_links)} CSV files to download")
            
            # Create aiohttp session with timeout
            timeout = aiohttp.ClientTimeout(total=config.request_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Create concurrent download tasks
                download_tasks = []
                for csv_url in csv_links:
                    task = self.download_csv_async(session, csv_url)
                    download_tasks.append(task)
                
                # Process downloads in batches to avoid overwhelming the server
                batch_size = config.concurrent_downloads
                completed = 0
                
                for i in range(0, len(download_tasks), batch_size):
                    batch = download_tasks[i:i+batch_size]
                    
                    if progress_callback:
                        progress = 10 + (completed * 60 // len(download_tasks))
                        await progress_callback(progress, f"Downloading batch {i//batch_size + 1} ({completed}/{len(download_tasks)} complete)")
                    
                    # Execute batch concurrently
                    batch_results = await asyncio.gather(*batch, return_exceptions=True)
                    
                    # Process results
                    for result in batch_results:
                        if isinstance(result, Exception):
                            logger.error(f"Download task failed: {result}")
                        elif result is not None:
                            all_data.append(result)
                        completed += 1
                    
                    # Small delay between batches to be respectful to server
                    if i + batch_size < len(download_tasks):
                        await asyncio.sleep(0.1)
            
            if progress_callback:
                await progress_callback(75, "Processing and combining data...")
            
            if not all_data:
                logger.warning("No valid data fetched from any CSV files")
                return pd.DataFrame()
            
            # Combine all dataframes, handling different column structures
            try:
                combined_df = pd.concat(all_data, ignore_index=True, sort=False)
            except Exception as e:
                logger.error(f"Error combining DataFrames: {e}")
                raise DataProcessingError(f"Failed to combine CSV data: {str(e)}")
            
            if progress_callback:
                await progress_callback(85, "Standardizing timestamps...")
            
            # Standardize timestamp column if it exists
            self._standardize_timestamps(combined_df)
            
            total_time = time.time() - start_time
            logger.info(f"Combined dataset: {len(combined_df)} rows, columns: {list(combined_df.columns)[:10]}{'...' if len(combined_df.columns) > 10 else ''}")
            logger.info(f"Total fetch time: {total_time:.2f}s, Success rate: {(len(all_data)/len(csv_links)*100):.1f}%")
            
            return combined_df
            
        except Exception as e:
            logger.error(f"Error in fetch_all_data_async: {e}")
            raise DataFetchError(f"Failed to fetch data: {str(e)}")
    
    def _standardize_timestamps(self, df: pd.DataFrame) -> None:
        """Standardize timestamp columns in DataFrame"""
        timestamp_cols = ['timestamp', 'time', 'datetime', 'date']
        for col in timestamp_cols:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    df.sort_values(col, inplace=True)
                    logger.info(f"Standardized timestamp column: {col}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to standardize timestamp column {col}: {e}")
                    continue
    
    def _restructure_data_vectorized(self, df: pd.DataFrame, target_numbers: List[int]) -> pd.DataFrame:
        """Efficiently restructure data using pandas vectorized operations"""
        try:
            # Base columns that apply to all targets
            base_cols = ['datetime', 'Date', 'Time', 'Timezone', 'IPAddress', 'source_file']
            base_data = df[base_cols].copy()
            
            all_target_data = []
            
            for target_num in target_numbers:
                # Get all columns for this target
                target_cols = {
                    'target': f'Target{target_num}',
                    'transmit': f'Transmit{target_num}',
                    'receive': f'Receive{target_num}',
                    'loss_pct': f'LossPct{target_num}',
                    'delay_min': f'DelayMin{target_num}',
                    'delay_avg': f'DelayAvg{target_num}',
                    'delay_max': f'DelayMax{target_num}'
                }
                
                # Check if target column exists
                if target_cols['target'] not in df.columns:
                    continue
                
                # Create a copy of base data for this target
                target_data = base_data.copy()
                target_data['target_number'] = target_num
                
                # Add target-specific columns
                for new_col, old_col in target_cols.items():
                    if old_col in df.columns:
                        target_data[new_col] = df[old_col]
                    else:
                        target_data[new_col] = None
                
                # Filter out DNS failures and invalid targets using vectorized operations
                if 'target' in target_data.columns:
                    # Create boolean mask for valid targets
                    valid_mask = (
                        target_data['target'].notna() &
                        ~target_data['target'].astype(str).str.startswith(DNS_FAILURE_PREFIX) &
                        (target_data['target'].astype(str) != '') &
                        (target_data['target'].astype(str) != 'nan')
                    )
                    
                    # Apply filter
                    target_data = target_data[valid_mask]
                    
                    if not target_data.empty:
                        all_target_data.append(target_data)
            
            if not all_target_data:
                logger.warning("No valid target data found after restructuring")
                return pd.DataFrame()
            
            # Combine all target data
            result_df = pd.concat(all_target_data, ignore_index=True)
            
            # Rename columns for consistency
            result_df.rename(columns={'IPAddress': 'ip_address'}, inplace=True)
            
            logger.info(f"Vectorized restructuring: {len(df)} rows -> {len(result_df)} target records")
            return result_df
            
        except Exception as e:
            logger.error(f"Error in vectorized restructuring: {e}")
            raise DataProcessingError(f"Failed to restructure data: {str(e)}")
    
    def fetch_all_data(self) -> pd.DataFrame:
        """Synchronous wrapper for backward compatibility"""
        return asyncio.run(self.fetch_all_data_async())
    
    async def get_ping_data_async(self, progress_callback=None) -> pd.DataFrame:
        """Extract and restructure target-based ping data from all CSV files with progress"""
        df = await self.fetch_all_data_async(progress_callback)
        
        if progress_callback:
            await progress_callback(90, "Restructuring data by targets...")
        
        if df.empty:
            return df
        
        # Create combined datetime column
        if 'Date' in df.columns and 'Time' in df.columns:
            df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
        
        # Identify target numbers (1-6 based on the data structure)
        target_numbers = []
        for col in df.columns:
            if col.startswith('Target') and col[6:].isdigit():
                target_numbers.append(int(col[6:]))
        
        target_numbers = sorted(set(target_numbers))
        logger.info(f"Found {len(target_numbers)} targets: {target_numbers}")
        
        if progress_callback:
            await progress_callback(95, "Filtering targets and organizing records...")
        
        # Restructure data to long format using vectorized operations
        ping_df = self._restructure_data_vectorized(df, target_numbers)
        
        # Convert numeric columns
        numeric_cols = ['transmit', 'receive', 'loss_pct', 'delay_min', 'delay_avg', 'delay_max']
        for col in numeric_cols:
            if col in ping_df.columns:
                ping_df[col] = pd.to_numeric(ping_df[col], errors='coerce')
        
        logger.info(f"Restructured ping data: {len(ping_df)} rows (targets x time points)")
        logger.info(f"Unique targets: {ping_df['target'].unique().tolist() if 'target' in ping_df.columns else 'None'}")
        
        return ping_df
    
    def get_ping_data(self) -> pd.DataFrame:
        """Synchronous wrapper for backward compatibility"""
        return asyncio.run(self.get_ping_data_async())
    
    async def get_dns_failure_data_async(self, progress_callback=None) -> pd.DataFrame:
        """Extract DNS failure events from all CSV files"""
        df = await self.fetch_all_data_async(progress_callback)
        
        if progress_callback:
            await progress_callback(90, "Collecting DNS failure events...")
        
        if df.empty:
            return pd.DataFrame()
        
        # Create combined datetime column
        if 'Date' in df.columns and 'Time' in df.columns:
            df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
        
        # Identify target numbers (1-6 based on the data structure)
        target_numbers = []
        for col in df.columns:
            if col.startswith('Target') and col[6:].isdigit():
                target_numbers.append(int(col[6:]))
        
        target_numbers = sorted(set(target_numbers))
        
        # Collect DNS failure events
        dns_failures = []
        base_cols = ['datetime', 'Date', 'Time', 'Timezone', 'IPAddress', 'source_file']
        
        for target_num in target_numbers:
            target_col = f'Target{target_num}'
            if target_col not in df.columns:
                continue
                
            # Find rows where this target has DNS failure
            dns_failure_mask = (
                df[target_col].notna() &
                df[target_col].astype(str).str.startswith(DNS_FAILURE_PREFIX)
            )
            
            if dns_failure_mask.any():
                failure_data = df[dns_failure_mask][base_cols].copy()
                failure_data['target_number'] = target_num
                failure_data['target'] = df[dns_failure_mask][target_col]
                failure_data['failure_type'] = 'DNS'
                dns_failures.append(failure_data)
        
        if dns_failures:
            result_df = pd.concat(dns_failures, ignore_index=True)
            logger.info(f"Found {len(result_df)} DNS failure events across {len(target_numbers)} targets")
            return result_df
        else:
            logger.info("No DNS failure events found")
            return pd.DataFrame()
    
    def get_dns_failure_data(self) -> pd.DataFrame:
        """Synchronous wrapper for DNS failure data"""
        return asyncio.run(self.get_dns_failure_data_async())
    
    def get_target_summary(self) -> pd.DataFrame:
        """Get summary of all targets being monitored"""
        df = self.fetch_all_data()
        
        if df.empty:
            return pd.DataFrame()
        
        # Get unique targets, excluding DNS failures
        targets = []
        for i in range(1, 7):  # Targets 1-6
            target_col = f'Target{i}'
            if target_col in df.columns:
                unique_targets = df[target_col].dropna().unique()
                for target in unique_targets:
                    # Skip DNS failures and invalid targets
                    if (not str(target).startswith('DNS:Failure') and 
                        str(target) != '' and 
                        str(target) != 'nan'):
                        targets.append({'target_number': i, 'target': target})
        
        return pd.DataFrame(targets).drop_duplicates()