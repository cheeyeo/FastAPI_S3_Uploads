#!/usr/bin/env bash


# Wait until the mongo-master responds
until mongosh --host mongo1 -u ${MONGO_DB_ROOT_USERNAME} -p ${MONGO_DB_ROOT_PASSWORD} --eval "db.adminCommand('ping')" > /dev/null 2>&1; do
  sleep 2
done

echo "mongo1 is ready. Initiating replica set..."

mongosh --host mongo1 -u ${MONGO_DB_ROOT_USERNAME} -p ${MONGO_DB_ROOT_PASSWORD} --eval "try { rs.status() } catch (err) { rs.initiate({_id:'rs0',members:[{_id:0,host:'mongo1:27017',priority:2},{_id:1,host:'mongo2:27017',priority:1},{_id:2,host:'mongo3:27017',priority:1}]});}"
