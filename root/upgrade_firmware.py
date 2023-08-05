from os import system, path
import datetime
import time

def upgrade_firmware(url):
    system(f'wget {url} -O /tmp/firmware.bin')
    system("sysupgrade /tmp/firmware.bin")

def main():
    if path.isfile("/tmp/update_time"):
        f = open("/tmp/update_time", "r")
        lines = f.readlines()
        date = lines[0][:-1]
        url = lines[1][:-1]
        update_date = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
        while True:
        
            now = datetime.datetime.utcnow()
            if now > update_date:
                upgrade_firmware(url)
                break
            else:
                time.sleep(int(update_date.timestamp() - now.timestamp()))



if __name__ == "__main__":
    main()
