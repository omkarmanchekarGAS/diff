#Considering the "one-and-done"-ness of this script, making it a class for only a subsequent single in
#instantiation seems weird

# Just make this read from a file or something else more sustainable
options = ["these messages are","contained","by a list that","expands the \"menu\" ", "as new messages are added",\
    "I may make them", "just pull related message choices from a", "txt file though"]
class CPInterface:
    def __init__(self):
        # for messages as they come from the central system
        self.cs_messages = []

    def menu(self):
        print(79*"#")
        print(5*"#" + 25*"/" + "*Message Options*" + 27*"/" + 5*"#")
        print(79*"#")
        for i in range(len(options)):
            buffer = (74-len(options[i])-len(str(i+1)))*" " + "#"
            print("# " + str(i+1) + ": " +options[i]+ buffer)
        print(79*"#" + "\n")
        #print('\033[1;36m' + 'Placeholder' + '\033[0m')

    def general_interface(self):
        pass

if __name__ == "__main__":
    interface = CPInterface()
    interface.menu()
        
