import rasterio as rio
import numpy as np
from osgeo import gdal, osr, ogr
import os

def get_spatial_reference_of_epsg_from_code(epsg_code):
    """Create spatial reference from EPSG code"""
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg_code)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs

def get_default_no_data_value_from_type(gdal_data_type):
    """Get appropriate no-data value for GDAL data type"""
    type_mapping = {
        gdal.GDT_Byte: 255,
        gdal.GDT_UInt16: 65535,
        gdal.GDT_Int16: -32768,
        gdal.GDT_UInt32: 4294967295,
        gdal.GDT_Int32: -2147483648,
        gdal.GDT_Float32: -9999.0,
        gdal.GDT_Float64: -9999.0
    }
    return type_mapping.get(gdal_data_type, -9999)

def export_sparse_to_tiff_dataset(template_raster, output_path, xcoords, ycoords, values):
    """Export sparse data to TIFF using template raster"""
    with rio.open(template_raster) as template:
        profile = template.profile.copy()
        transform = template.transform
        
    output_array = np.full((profile['height'], profile['width']), profile['nodata'], dtype=profile['dtype'])
    
    rows, cols = rio.transform.rowcol(transform, xcoords, ycoords)
    
    valid_indices = (rows >= 0) & (rows < profile['height']) & (cols >= 0) & (cols < profile['width'])
    output_array[rows[valid_indices], cols[valid_indices]] = values[valid_indices]
    
    with rio.open(output_path, 'w', **profile) as dst:
        dst.write(output_array, 1)

def get_minimum_spanning_extent_from_biogeographic_regions(biogeographic_file):
    """Get minimum spanning extent from biogeographic regions"""
    import geopandas as gpd
    
    if biogeographic_file.endswith('.shp'):
        gdf = gpd.read_file(biogeographic_file)
        bounds = gdf.total_bounds
        return {
            'minx': bounds[0],
            'miny': bounds[1], 
            'maxx': bounds[2],
            'maxy': bounds[3]
        }
    else:
        with rio.open(biogeographic_file) as src:
            bounds = src.bounds
            return {
                'minx': bounds.left,
                'miny': bounds.bottom,
                'maxx': bounds.right, 
                'maxy': bounds.top
            }
