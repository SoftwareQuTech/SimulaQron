
ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9

python aliceTest.py &
python bobTest.py &
python eveTest.py &
