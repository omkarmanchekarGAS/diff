while [ 1 -eq 1 ]
do
ifconfig | grep ppp-wan2 | grep -v grep
if [ $? -eq 0 ]; then
echo "cell connected"
python3 set_cell_connected.py
else
service network restart
python3 set_cell_disconnected.py
fi
sleep 150
ping -c 1 google.com
if [ $? -eq 0 ]; then
echo "we have internet"
else
ps | grep pppd | grep -v grep | awk '{print $1}' | xargs kill
python3 set_cell_disoconnected.py
fi
sleep 150
done
