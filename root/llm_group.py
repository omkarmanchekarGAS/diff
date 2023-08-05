import json

def parse_llm():
    f = open('llm.json')
    items = json.load(f)
    f.close()
    groups = []
    q=items['groups']
    #print(q)
    for i in q:
        #print(i)
        if(len(i['members'])*6 > i['maxCurrent']):
            return -1
        new_item = (i['members'],i['maxCurrent'])
        groups.append(new_item)
    #print(groups)
    return groups

class child():
    current_current = 0
    next_current = 0
    active = 0

    def __init__(self):
        self.current_current = 0
        self.next_current = 0
        self.active = 1
    
    def update_current(self):
        self.current_current = self.next_current
        self.next_current = 6

    def update_next_current(self, new_current):
        self.next_current = new_current
    
    def update_activity(self, activity):
        self.active = activity

        
class llm_group():
    #dictionary of serial nums of group members (parent included)
    members = {}
    max_current = 0
    decreases = {}

    #expects list of serial nums to assign to children and parent (if in group), max current of entire group
    def __init__(self, mems, maxc):
        for m in mems:
            self.members[m] = child()
        self.max_current = maxc
        self.decreases = {}

    #calculates the current that each member of the group should have, taking parent into account
    #stores these values in each child's next_current field
    #returns the current that should be assigned to the parent, -1 if parent not in group, 0 if no members are active
    def calculate_current(self):
        #if extra_current is negative the site is not set up correctly or the json file is wrong
        extra_current = (self.max_current - (6*len(self.members)))
        num_active = 0
        
        for m in self.members:
            if self.members[m].active == 1:
                num_active = num_active + 1

        if num_active == 0:
            return
        
        extra_current = int(extra_current/num_active)
        print(len(self.members))
        for m in self.members:
            if self.members[m].active == 1:
                self.members[m].update_next_current(6 + extra_current)
            else:
                self.members[m].update_next_current(6)
            if self.members[m].next_current < self.members[m].current_current:
                self.decreases[m] = self.members[m].next_current
            print(str(m) + " " + str(self.members[m].active))
            
    def update_current(self, snum):
        self.members[snum].update_current()
        if snum in self.decreases.keys():
            self.decreases.pop(snum)
            
    def update_activity(self,snum,activity):
        self.members[snum].update_activity(activity)

    def contains(self,snum):
        return snum in self.members.keys()
    
    def sort_currents(self):
        currents = {}
        for m in self.members:
            currents[m] = self.members[m].next_current - self.members[m].current_current
        return sorted(currents.items(), key=lambda x:x[1])