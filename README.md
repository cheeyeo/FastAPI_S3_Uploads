### FastAPI File Uploads

Learning how to use FastAPI for file uploads to S3



#### Ref

* https://oneuptime.com/blog/post/2026-01-26-fastapi-file-uploads/view#upload-progress-tracking

* https://oneuptime.com/blog/post/2026-02-02-fastapi-file-uploads/view

* https://betterstack.com/community/guides/scaling-python/uploading-files-using-fastapi/

* https://docs.aws.amazon.com/boto3/latest/_modules/boto3/s3/transfer.html


( upload larget files using boto3 s3 transferconfig )
* https://cloudplexo.com/blog/uploading-large-files-upto-5tb-to-amazon-s3-using-boto3-in-python/

### TODO
https://celery.school/celery-progress-bars-with-fastapi-htmx
https://github.com/bstiel/celery-task-progress-bar


* Redo validator into separate module using pydantic basemodel?
* Return response model


https://testdriven.io/blog/fastapi-mongo-websockets/#database-listener



#### MONGODB

```
docker exec -it fastapi_file_upload-mongo-1 mongosh -u root -p example
```

```
MongoDB Change Streams require a replica set. According to MongoDB, a replica set in MongoDB is a group of mongod processes that maintain the same data set, providing redundancy and high availability.
```

to create single node replicaset with keyfile refer to here:

( BELOW NOT WORKING )
https://stackoverflow.com/questions/61486024/mongo-container-with-a-replica-set-with-only-one-node-in-docker-compose


( BELOW NOT WORKIGN )
https://stackoverflow.com/questions/76013265/how-to-do-a-mongodb-6-single-node-replicaset-with-docker-compose


( NOT WORKING )
https://dev.to/denisakp/setting-up-a-3-node-mongodb-replica-set-cluster-with-docker-compose-50kn


( WORKS BUT ONLY IN SCRIPT WITHOUT AUTH )
https://www.mongodb.com/resources/products/compatibilities/deploying-a-mongodb-cluster-with-docker

( THIS IS THE ONLY ONE THAT WORKS )
https://medium.com/@ravikushwaha18.rk/setting-up-a-mongodb-replica-set-with-docker-compose-62ece5c295a1


NEED TO UPDATE THE /etc/hosts file else the client code won't work....


https://anthonysimmon.com/the-only-local-mongodb-replica-set-with-docker-compose-guide-youll-ever-need/


React typescript progress bar
https://dev.to/simonnystrom/building-a-progress-bar-222n



#### TODO:

Issue is the mongodb changeset works but the updates to the UI via WS happens only after the file is uploaded

need the progresscallback to use async mongodb client which means we need to use an async S3 client....