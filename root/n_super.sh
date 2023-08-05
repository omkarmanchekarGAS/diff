while [ 1 -eq 1 ]
do
ps -w | grep central_system | grep -v grep
if [ $? -eq 0 ]; then
echo "its there"
else
python /root/ocpp/src/connect_to_central_system.py 0 &
fi
sleep 1
done

