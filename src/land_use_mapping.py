"""
Land Use Classification Mapping
Based on CORINE Land Cover classification system
"""

CORINE_TO_CLASS = {
    111: 1,   # Continuous urban fabric -> Urban
    112: 1,   # Discontinuous urban fabric -> Urban
    121: 2,   # Industrial or commercial units -> Industrial
    122: 0,   # Road and rail networks -> null
    123: 0,   # Port areas -> null
    124: 0,   # Airports -> null
    131: 0,   # Mineral extraction sites -> null
    132: 0,   # Dump sites -> null
    133: 0,   # Construction sites -> null
    141: 0,   # Green urban areas -> null
    142: 0,   # Sport and leisure facilities -> null
    211: 3,   # Non-irrigated arable land -> Arable
    212: 3,   # Permanently irrigated land -> Arable
    213: 3,   # Rice fields -> Arable
    221: 4,   # Vineyards -> PermanentCrops
    222: 4,   # Fruit trees and berry plantations -> PermanentCrops
    223: 4,   # Olive groves -> PermanentCrops
    231: 5,   # Pastures -> Pastures
    241: 3,   # Annual crops associated with permanent crops -> Arable
    242: 3,   # Complex cultivation patterns -> Arable
    243: 3,   # Land principally occupied by agriculture -> Arable
    244: 5,   # Agro-forestry areas -> Pastures
    311: 6,   # Broad-leaved forest -> ForestsMature
    312: 6,   # Coniferous forest -> ForestsMature
    313: 6,   # Mixed forest -> ForestsMature
    321: 7,   # Natural grasslands -> TransWoodlandShrub
    322: 7,   # Moors and heathland -> TransWoodlandShrub
    323: 7,   # Sclerophyllous vegetation -> TransWoodlandShrub
    324: 15,  # Transitional woodland-shrub -> ForestYoung
    331: 14,  # Beaches - dunes - sands -> SHVA
    332: 14,  # Bare rocks -> SHVA
    333: 14,  # Sparsely vegetated areas -> SHVA
    334: 7,   # Burnt areas -> TransWoodlandShrub
    335: 0,   # Glaciers and perpetual snow -> null
    411: 0,   # Inland marshes -> null
    412: 0,   # Peat bogs -> null
    421: 0,   # Salt marshes -> null
    422: 0,   # Salines -> null
    423: 0,   # Intertidal flats -> null
    511: 0,   # Water courses -> null
    512: 0,   # Water bodies -> null
    521: 0,   # Coastal lagoons -> null
    522: 0,   # Estuaries -> null
    523: 0,   # Sea and ocean -> null
    999: 999, # NODATA -> nodata
}

CLASS_DESCRIPTIONS = {
    0: "null",
    1: "Urban",
    2: "Industrial", 
    3: "Arable",
    4: "PermanentCrops",
    5: "Pastures",
    6: "ForestsMature",
    7: "TransWoodlandShrub",
    14: "SHVA",
    15: "ForestYoung",
    999: "nodata"
}

CROPLAND_CORINE_CODES = [211, 212, 213, 241, 242, 243]

def get_class_from_corine(corine_code):
    """Convert CORINE land cover code to simplified class"""
    return CORINE_TO_CLASS.get(corine_code, 999)

def get_cropland_transitions():
    """Get all possible transitions to cropland (class 3)"""
    transitions = []
    for from_class in range(16):  # 0-15 possible classes
        if from_class != 3:  # Not already cropland
            transitions.append(f"{from_class}3")  # transition to class 3
    return transitions

def is_cropland_transition(transition_code):
    """Check if transition code represents a change to cropland"""
    if isinstance(transition_code, str):
        return transition_code.endswith('3')
    return str(transition_code).endswith('3')
