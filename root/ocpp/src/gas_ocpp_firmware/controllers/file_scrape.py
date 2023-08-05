from hardware_json import Hardware_JSON
import locking
filename = input("Input some filename: ")
lines = []
with open(filename) as f:
    while True:
        line = f.readline()
        if not line:
            break
        lines.append(line.strip('\n').split(' '))
    f.close()

state = Hardware_JSON("LED")
print()
count = 0 
with open('writeto.txt','a') as f:
    while len(lines)>0 :
        if count>2:
            f.close
            locking.lock_file(f)
        state.add(lines[0][0],float(lines[0][1]))
        if len(state.info_()) > 4:
            f.write(state.get_json())
            f.write('\n')
            #print(state.get_json()+'\n')
            state.empty()
            count+=1
        lines.pop(0)
    if len(state.info_()) > 0:
            f.write(state.get_json())
            f.write('\n')
            locking.unlock_file(f)
            f.close
            #print(state.get_json()