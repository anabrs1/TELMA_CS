#!/usr/bin/env python3
"""
Test script for land use classification mapping
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from land_use_mapping import *
import yaml

def test_land_use_mapping():
    """Test land use classification mapping"""
    print('Testing land use classification mapping...')
    
    test_codes = [211, 311, 111, 999]
    for code in test_codes:
        class_id = get_class_from_corine(code)
        description = CLASS_DESCRIPTIONS.get(class_id, 'Unknown')
        print(f'CORINE {code} -> Class {class_id} ({description})')
    
    print(f'Total CORINE codes mapped: {len(CORINE_TO_CLASS)}')
    
    test_transitions = ['13', '23', '56', '73']
    for trans in test_transitions:
        is_cropland = is_cropland_transition(trans)
        print(f'Is {trans} a cropland transition? {is_cropland}')
    
    print(f'Cropland CORINE codes: {CROPLAND_CORINE_CODES}')
    
    return True

def test_config_loading():
    """Test configuration file loading"""
    print('\nTesting configuration loading...')
    
    try:
        with open('config/default_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print(f'Config loaded successfully')
        print(f'Land use classes mapped: {len(config["land_use"]["class_mapping"])}')
        print(f'All classes: {config["land_use"]["all_classes"]}')
        print(f'Cropland codes: {config["land_use"]["cropland_codes"]}')
        
        return True
    except Exception as e:
        print(f'Config loading failed: {e}')
        return False

if __name__ == "__main__":
    print("Land Use Change Modeling System - Classification Test")
    print("=" * 60)
    
    success = True
    success &= test_land_use_mapping()
    success &= test_config_loading()
    
    print("\n" + "=" * 60)
    if success:
        print("All tests passed!")
    else:
        print("Some tests failed!")
    
    sys.exit(0 if success else 1)
