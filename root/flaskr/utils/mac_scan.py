# import objc
# import argparse
# from pprint import pprint


# def scan(concrete_ssid=None):
#     print("Running Function")
#     bundle_path = '/System/Library/Frameworks/CoreWLAN.framework'
#     objc.loadBundle('CoreWLAN',
#                     bundle_path=bundle_path,
#                     module_globals=globals())

#     iface = CWInterface.interface()
#     networks = iface.scanForNetworksWithName_includeHidden_error_(concrete_ssid, True, None)
    
#     return [
#         i.ssid()
#         for i in networks[0].allObjects() if i.ssid() is not None
#     ]



