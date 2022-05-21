def get_summary(OF, HI, alpha):
    text = '''
    Compute primary cracking for a given Organo Facies and Heating rate

    You can call it programatically (The code snippet below is up to date with the current app values !):  

    ```python
    import pydaisi as pyd
    import pandas as pd

    primary_cracking = pyd.Daisi("Primary Cracking")
    result = primary_cracking.compute_cracking(OF="''' 
    text += str(OF) + '", HI=' + str(HI) + ', alpha=' + str(alpha) + ''').value
    
    df = result[0]
    ```
    '''


    return text
