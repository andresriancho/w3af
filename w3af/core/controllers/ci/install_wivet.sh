#!/bin/bash -x

if [ ! -d "wivet-svn" ]; then
    svn checkout http://wivet.googlecode.com/svn/trunk/ wivet-svn
fi

# Update to the latest revision
cd wivet-svn/
svn update

# Setup the database
cd wivet/
mysql -u ubuntu < wivet.sql

# Let the rest of the world know where we'll listen
echo 'localhost:8899' > /tmp/wivet.txt
