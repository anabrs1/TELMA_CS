#!/usr/bin/env python3
"""
CORINE Data Downloader

Downloads CORINE Land Cover (CLC) and CORINE Land Cover Change (CHA) data
from the Copernicus ArcGIS REST API for user-defined regions in EPSG:3035.

Usage:
    python download_corine_data.py --region andalucia --bbox 2840000 2200000 3140000 2500000
    python download_corine_data.py --region andalucia --bbox 2840000 2200000 3140000 2500000 --layers clc
    python download_corine_data.py --region andalucia --bbox 2840000 2200000 3140000 2500000 --layers cha
"""

import os
import argparse
import requests
import rasterio
from pathlib import Path
from tqdm import tqdm
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CORINE_LAYERS = {
    'clc_2000': 'https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2000_WM/MapServer/0',
    'clc_2006': 'https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2006_WM/MapServer/0',
    'clc_2012': 'https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2012_WM/MapServer/0',
    'clc_2018': 'https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer/0',
    'cha_1990_2000': 'https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CHA1990_2000_WM/MapServer/0',
    'cha_2000_2006': 'https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CHA2000_2006_WM/MapServer/0',
    'cha_2006_2012': 'https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CHA2006_2012_WM/MapServer/0',
    'cha_2012_2018': 'https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CHA2012_2018_WM/MapServer/0',
}

def download_corine_layer(layer_key, layer_url, region_name, bbox, output_dir, image_size=(1024, 1024)):
    """
    Download a single CORINE layer as GeoTIFF
    
    Args:
        layer_key (str): Layer identifier (e.g., 'clc_2000')
        layer_url (str): ArcGIS REST service URL
        region_name (str): Name of the region for filename
        bbox (list): Bounding box [xmin, ymin, xmax, ymax] in EPSG:3035
        output_dir (str): Output directory path
        image_size (tuple): Image size (width, height)
    """
    
    filename = f"{region_name}_{layer_key}.png"
    filepath = os.path.join(output_dir, filename)
    
    if os.path.exists(filepath):
        logger.info(f"File {filename} already exists, skipping download")
        return True
    
    params = {
        'bbox': f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
        'bboxSR': '3035',
        'imageSR': '3035',
        'f': 'image',
        'format': 'png',
        'size': f"{image_size[0]},{image_size[1]}"
    }
    
    export_url = f"{layer_url.replace('/MapServer/0', '/MapServer/export')}"
    
    try:
        logger.info(f"Downloading {layer_key} for {region_name}...")
        
        response = requests.get(export_url, params=params, timeout=300)
        response.raise_for_status()
        
        if response.status_code != 200:
            logger.error(f"HTTP error {response.status_code} for {layer_key}")
            return False
        
        if len(response.content) < 1000:
            logger.error(f"Response too small for {layer_key}: {len(response.content)} bytes")
            return False
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        try:
            file_size = os.path.getsize(filepath)
            if file_size < 1000:
                logger.error(f"Downloaded file {filename} is too small ({file_size} bytes)")
                os.remove(filepath)
                return False
            logger.info(f"Successfully downloaded {filename} - Size: {file_size} bytes")
        except Exception as e:
            logger.error(f"Error checking downloaded file {filename}: {e}")
            os.remove(filepath)
            return False
        
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {layer_key}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {layer_key}: {e}")
        return False

def download_corine_data(region_name, bbox, output_dir="input", layers="all", image_size=(1024, 1024), proxy_config=None):
    """
    Download CORINE data for a specified region
    
    Args:
        region_name (str): Name of the region
        bbox (list): Bounding box [xmin, ymin, xmax, ymax] in EPSG:3035
        output_dir (str): Output directory
        layers (str): Which layers to download ('all', 'clc', 'cha')
        image_size (tuple): Image size (width, height)
        proxy_config (dict): Proxy configuration with 'http' and 'https' keys
    """
    
    if proxy_config:
        if 'http' in proxy_config:
            os.environ['http_proxy'] = proxy_config['http']
        if 'https' in proxy_config:
            os.environ['https_proxy'] = proxy_config['https']
        logger.info("Proxy configuration applied")
    
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {os.path.abspath(output_dir)}")
    
    if layers == "clc":
        selected_layers = {k: v for k, v in CORINE_LAYERS.items() if k.startswith('clc_')}
    elif layers == "cha":
        selected_layers = {k: v for k, v in CORINE_LAYERS.items() if k.startswith('cha_')}
    else:
        selected_layers = CORINE_LAYERS
    
    logger.info(f"Downloading {len(selected_layers)} layers for region: {region_name}")
    logger.info(f"Bounding box (EPSG:3035): {bbox}")
    
    successful_downloads = 0
    failed_downloads = []
    
    for layer_key, layer_url in tqdm(selected_layers.items(), desc="Downloading layers"):
        success = download_corine_layer(
            layer_key, layer_url, region_name, bbox, output_dir, image_size
        )
        
        if success:
            successful_downloads += 1
        else:
            failed_downloads.append(layer_key)
    
    logger.info(f"\nDownload Summary:")
    logger.info(f"Successful downloads: {successful_downloads}/{len(selected_layers)}")
    
    if failed_downloads:
        logger.warning(f"Failed downloads: {failed_downloads}")
    else:
        logger.info("All downloads completed successfully!")
    
    return successful_downloads, failed_downloads

def main():
    parser = argparse.ArgumentParser(description='Download CORINE Land Cover data')
    parser.add_argument('--region', required=True, help='Region name for filename')
    parser.add_argument('--bbox', nargs=4, type=float, required=True, 
                       metavar=('XMIN', 'YMIN', 'XMAX', 'YMAX'),
                       help='Bounding box in EPSG:3035 (xmin ymin xmax ymax)')
    parser.add_argument('--output-dir', default='input', 
                       help='Output directory (default: input)')
    parser.add_argument('--layers', choices=['all', 'clc', 'cha'], default='all',
                       help='Which layers to download (default: all)')
    parser.add_argument('--size', nargs=2, type=int, default=[1024, 1024],
                       metavar=('WIDTH', 'HEIGHT'),
                       help='Image size in pixels (default: 1024 1024)')
    parser.add_argument('--proxy-user', help='Proxy username')
    parser.add_argument('--proxy-pass', help='Proxy password')
    parser.add_argument('--proxy-host', default='ps-sev-usr.cec.eu.int:8012',
                       help='Proxy host:port (default: ps-sev-usr.cec.eu.int:8012)')
    
    args = parser.parse_args()
    
    proxy_config = None
    if args.proxy_user and args.proxy_pass:
        proxy_url = f"http://{args.proxy_user}:{args.proxy_pass}@{args.proxy_host}"
        proxy_config = {
            'http': proxy_url,
            'https': proxy_url
        }
        logger.info(f"Using proxy: {args.proxy_host}")
    
    successful, failed = download_corine_data(
        region_name=args.region,
        bbox=args.bbox,
        output_dir=args.output_dir,
        layers=args.layers,
        image_size=tuple(args.size),
        proxy_config=proxy_config
    )
    
    if failed:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    if len(os.sys.argv) == 1:
        print("Example usage:")
        print("python download_corine_data.py --region andalucia --bbox 2840000 2200000 3140000 2500000")
        print("python download_corine_data.py --region andalucia --bbox 2840000 2200000 3140000 2500000 --layers clc")
        print("python download_corine_data.py --region andalucia --bbox 2840000 2200000 3140000 2500000 --layers cha")
        
        print("\nRunning example for Andalucía...")
        download_corine_data(
            region_name="andalucia",
            bbox=[2840000, 2200000, 3140000, 2500000],
            output_dir="input",
            layers="all"
        )
    else:
        main()
