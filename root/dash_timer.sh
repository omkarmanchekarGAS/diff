sleep 3600
uci set wireless.dashboard.disabled=1
uci commit
ps | grep '{flask}' | grep -v grep | awk '{print $1}' | xargs kill
