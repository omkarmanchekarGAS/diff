while [ 1 -eq 1 ]
do
d=$(($(date +%s)-$(date -r /tmp/i2cflag +%s)))
if [ $d -gt 20 ]; then
ps | grep i2cDriver | grep -v grep | awk '{print $1}' | xargs kill
python /root/i2cDriver.py &
fi
ps -w | grep central_system | grep -v grep
if [ $? -eq 0 ]; then
echo "its there"
logger -e "WATCHDOG" "its there"
else
python /root/ocpp/src/connect_to_central_system.py 0 &
fi
ps -w | grep ppp-wan2 | grep -v grep
if [ $? -eq 0 ]; then
echo 'got wan2'
logger -e "WATCHDOG" "got wan2"
else
ifup wan2
fi
sleep 10
done