psql -U postgres -h localhost -c 'drop database if exists rhodecode;'
psql -U postgres -h localhost -c 'create database rhodecode;'
paster setup-rhodecode rc.ini --force-yes --user=marcink --password=qweqwe --email=marcin@python-blog.com --repos=/home/marcink/repos --no-public-access
API_KEY=`psql -R " " -A -U postgres -h localhost -c "select api_key from users where admin=TRUE" -d rhodecode | awk '{print $2}'`
echo "run those after running server"
paster serve rc.ini --pid-file=rc.pid --daemon
sleep 3
rhodecode-api --apikey=$API_KEY --apihost=http://127.0.0.1:5001 create_user username:demo1 password:qweqwe email:demo1@rhodecode.org
rhodecode-api --apikey=$API_KEY --apihost=http://127.0.0.1:5001 create_user username:demo2 password:qweqwe email:demo2@rhodecode.org
rhodecode-api --apikey=$API_KEY --apihost=http://127.0.0.1:5001 create_user username:demo3 password:qweqwe email:demo3@rhodecode.org
rhodecode-api --apikey=$API_KEY --apihost=http://127.0.0.1:5001 create_users_group group_name:demo12
rhodecode-api --apikey=$API_KEY --apihost=http://127.0.0.1:5001 add_user_to_users_group usersgroupid:demo12 userid:demo1
rhodecode-api --apikey=$API_KEY --apihost=http://127.0.0.1:5001 add_user_to_users_group usersgroupid:demo12 userid:demo2
echo "killing server"
kill `cat rc.pid`
rm rc.pid
