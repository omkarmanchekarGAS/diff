import json
#Needed for hardware-related indications through: ILIM, Relay Status, Relay Control, LCD Message, LED State, NFC
class Hardware_JSON():
    def __init__(self, component):
        self.component= component
        self.info = dict()
    def info_(self):
        return self.info
    def add(self,key, data):
        if key not in self.info:
            self.info[key] = [data]
        else:
            self.info[key].append(data)

    def remove(self,key):
        self.info.pop(key,None)

    def empty(self):
        self.info.clear()
    #This function would be for automatically formatting a dict to be properly jsonized to serve a specific purpose depending on what it would be an indicator for
    def map_component(self):
        pass
    def get_json(self):
        return json.dumps(self.info)


if __name__ == "__main__":
    lcd_ = Hardware_JSON("lcd")
    lcd_.add("fault","screen")
    lcd_.add("fault","screen2")
    print(lcd_.get_json(0))