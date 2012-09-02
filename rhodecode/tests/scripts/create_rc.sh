psql -U postgres -h localhost -c 'drop database if exists rhodecode;'
psql -U postgres -h localhost -c 'create database rhodecode;'
paster setup-rhodecode rc.ini -q --user=marcink --password=qweqwe --email=marcin@python-blog.com --repos=/home/marcink/repos
API_KEY=`psql -R " " -A -U postgres -h localhost -c "select api_key from users where admin=TRUE" -d rhodecode | awk '{print $2}'`
echo "run those after running server"
echo "rhodecode-api --apikey=$API_KEY --apihost=http://127.0.0.1:5001 create_user username:demo1 password:qweqwe email:demo1@rhodecode.org"
echo "rhodecode-api --apikey=$API_KEY --apihost=http://127.0.0.1:5001 create_user username:demo2 password:qweqwe email:demo2@rhodecode.org"
echo "rhodecode-api --apikey=$API_KEY --apihost=http://127.0.0.1:5001 create_user username:demo3 password:qweqwe email:demo3@rhodecode.org"
echo "rhodecode-api --apikey=$API_KEY --apihost=http://127.0.0.1:5001 create_users_group group_name:demo12"
echo "rhodecode-api --apikey=$API_KEY --apihost=http://127.0.0.1:5001 add_user_to_users_group usersgroupid:demo12 userid:demo1"
echo "rhodecode-api --apikey=$API_KEY --apihost=http://127.0.0.1:5001 add_user_to_users_group usersgroupid:demo12 userid:demo2"

