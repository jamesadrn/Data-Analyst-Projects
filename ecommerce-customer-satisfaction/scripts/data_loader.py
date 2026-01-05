"""
Data Loader Utility for Olist E-commerce Dataset
This script provides functions to load and manage multiple CSV datasets with progress tracking.
"""

import os
import pandas as pd
from typing import Dict, Optional
import sys


def load_data(data_path: str, verbose: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Load all Olist datasets from the specified directory.
    
    Parameters:
    -----------
    data_path : str
        Path to the directory containing the CSV files
    verbose : bool, default=True
        Whether to print loading progress
        
    Returns:
    --------
    Dict[str, pd.DataFrame]
        Dictionary containing all loaded dataframes with dataset names as keys
        
    Raises:
    -------
    FileNotFoundError
        If the data_path directory doesn't exist
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data path not found: {data_path}")
    
    datasets = {
        'customers': 'olist_customers_dataset.csv',
        'geolocation': 'olist_geolocation_dataset.csv',
        'order_items': 'olist_order_items_dataset.csv',
        'orders': 'olist_orders_dataset.csv',
        'order_payments': 'olist_order_payments_dataset.csv',
        'order_reviews': 'olist_order_reviews_dataset.csv',
        'products': 'olist_products_dataset.csv',
        'sellers': 'olist_sellers_dataset.csv',
        'product_category_name_translation': 'product_category_name_translation.csv'
    }
    
    data_frames = {}
    total_datasets = len(datasets)
    failed_datasets = []
    
    for i, (name, file) in enumerate(datasets.items(), start=1):
        try:
            file_path = os.path.join(data_path, file)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file}")
            
            data_frames[name] = pd.read_csv(file_path)
            
            if verbose:
                percentage = (i / total_datasets) * 100
                print(f"[{percentage:5.1f}%] Loaded {name} ({i}/{total_datasets}) - {len(data_frames[name]):,} rows")
                
        except FileNotFoundError as e:
            failed_datasets.append((name, str(e)))
            if verbose:
                print(f"[ERROR] {name}: File not found - {file}")
                
        except pd.errors.EmptyDataError as e:
            failed_datasets.append((name, "Empty CSV file"))
            if verbose:
                print(f"[ERROR] {name}: Empty CSV file")
                
        except pd.errors.ParserError as e:
            failed_datasets.append((name, f"Parse error - {str(e)}"))
            if verbose:
                print(f"[ERROR] {name}: Failed to parse CSV - {str(e)}")
                
        except Exception as e:
            failed_datasets.append((name, str(e)))
            if verbose:
                print(f"[ERROR] {name}: {str(e)}")
    
    # Summary
    if verbose:
        print("\n" + "="*60)
        print(f"Loading complete: {len(data_frames)}/{total_datasets} datasets loaded successfully")
        
        if failed_datasets:
            print(f"\n{len(failed_datasets)} dataset(s) failed to load:")
            for name, error in failed_datasets:
                print(f"  - {name}: {error}")
        
        print("="*60)
    
    return data_frames


def get_dataset_info(data_frames: Dict[str, pd.DataFrame]) -> None:
    """
    Display information about loaded datasets.
    
    Parameters:
    -----------
    data_frames : Dict[str, pd.DataFrame]
        Dictionary of loaded dataframes
    """
    print("\nDataset Information:")
    print("="*80)
    print(f"{'Dataset':<40} {'Rows':>12} {'Columns':>10} {'Memory':>15}")
    print("-"*80)
    
    total_rows = 0
    total_memory = 0
    
    for name, df in data_frames.items():
        memory_mb = df.memory_usage(deep=True).sum() / 1024**2
        total_rows += len(df)
        total_memory += memory_mb
        print(f"{name:<40} {len(df):>12,} {len(df.columns):>10} {memory_mb:>12.2f} MB")
    
    print("-"*80)
    print(f"{'TOTAL':<40} {total_rows:>12,} {'':<10} {total_memory:>12.2f} MB")
    print("="*80)


if __name__ == "__main__":
    # Set data path
    DATA_PATH = "../data/raw" 
    
    # Load all datasets
    print("Loading Olist datasets...\n")
    data = load_data(DATA_PATH, verbose=True)
    
    # Display dataset information
    get_dataset_info(data)