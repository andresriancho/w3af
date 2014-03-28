USE mysql;

UPDATE user set password=PASSWORD("testpass") where User='root';
FLUSH privileges;
