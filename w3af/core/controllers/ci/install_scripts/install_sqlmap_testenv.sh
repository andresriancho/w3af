#!/bin/bash -x

if [ ! -d "sqlmap-testenv" ]; then
    git clone https://github.com/sqlmapproject/testenv.git sqlmap-testenv
fi

# Change the mysql database password
mysql -u ubuntu < w3af/core/controllers/ci/helpers/set_root_password.sql

# Update to the latest revision
cd sqlmap-testenv/
git pull
git checkout master

# Create the DB, using the new password
mysql -u root -ptestpass < schema/mysql.sql

# Let the rest of the world know where we'll listen
echo 'localhost:8998' > /tmp/sqlmap_testenv.txt

# The service itself is started in circle.yml