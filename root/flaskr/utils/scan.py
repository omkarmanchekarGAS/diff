import os

def get_cell():
    """
    Get the wifi names available to connect in a sorted order.
    Returns:
    A list of strings containing the names of the cells.    
    """
    wifi_names = os.popen("iw wlan0 scan| grep SSID").read()
    wifi_names = wifi_names.split('\n') 
    print(wifi_names)
    wifi_names = [i[7:] for i in wifi_names ]
    wifi_names = wifi_names[:-1]
    wifis = []
    [wifis.append(x) for x in wifi_names if x not in wifis]

    print(str(wifi_names))
    return str(wifis)


