'''
Components package

Handles individual object representation of WinGem packets
'''

# The inside (Basic 1) screen of test2screens.txt
# has a 2.3 ratio (width:height) in AFW
# so keep the values below scaled to that

# Constants for all components
HEIGHTEMSCALE = 1 * 1.75
WIDTHEMSCALE = 0.4 * 1.75

def applyscaling(value: float, height: bool):
    ''' apply scaling to value '''
    if height:
        scaling = HEIGHTEMSCALE
    else:
        scaling = WIDTHEMSCALE
    # round it to a single digit
    return round(scaling * value, 1)
