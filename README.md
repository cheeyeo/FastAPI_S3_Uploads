### FastAPI File Uploads

Learning how to use FastAPI for file uploads to S3 which includes a ReactUI that shows realtime updates via websocket from the API

The updates are provided via MongoDB changesets and can run locally in docker containers.



### REF
* https://testdriven.io/blog/fastapi-mongo-websockets/#database-listener

* https://oneuptime.com/blog/post/2026-01-26-fastapi-file-uploads/view#upload-progress-tracking

* https://oneuptime.com/blog/post/2026-02-02-fastapi-file-uploads/view

* https://betterstack.com/community/guides/scaling-python/uploading-files-using-fastapi/

* https://python.plainenglish.io/handling-file-uploads-in-fastapi-from-basics-to-s3-integration-fc7e64f87d65

* https://docs.aws.amazon.com/boto3/latest/_modules/boto3/s3/transfer.html

( upload larget files using boto3 s3 transferconfig )
* https://cloudplexo.com/blog/uploading-large-files-upto-5tb-to-amazon-s3-using-boto3-in-python/


#### MONGODB ON DOCKER

```
docker exec -it fastapi_file_upload-mongo-1 mongosh -u root -p example
```

On mongodb init scripts not loading to create initial database:

  If the /data/db volume already exists the init scripts won't run

  Also need to mount the directory the script is in and not the script itself..


MongoDB Change Streams require a replica set. According to MongoDB, a replica set in MongoDB is a group of mongod processes that maintain the same data set, providing redundancy and high availability.


( WORKS BUT ONLY IN SHELL SCRIPT WITHOUT AUTH )
https://www.mongodb.com/resources/products/compatibilities/deploying-a-mongodb-cluster-with-docker

( THIS IS THE ONLY ONE THAT WORKS )

NEED TO UPDATE THE /etc/hosts file else the client code won't work....
https://medium.com/@ravikushwaha18.rk/setting-up-a-mongodb-replica-set-with-docker-compose-62ece5c295a1

https://anthonysimmon.com/the-only-local-mongodb-replica-set-with-docker-compose-guide-youll-ever-need/


#### Generate large file for testing uploads
use dd on ubuntu

```
#kilobytes
dd if=/dev/zero of=filename bs=1 count=0 seek=200K

#megabytes
dd if=/dev/zero of=filename bs=1 count=0 seek=200M

#gigabytes
dd if=/dev/zero of=filename bs=1 count=0 seek=200G

#terabytes
dd if=/dev/zero of=filename bs=1 count=0 seek=200T

```

#### ASYNC

* https://stackoverflow.com/questions/72092993/i-want-to-use-boto3-in-async-function-python

* https://joelmccoy.medium.com/python-and-boto3-performance-adventures-synchronous-vs-asynchronous-aws-api-interaction-22f625ec6909

https://betterstack.com/community/guides/scaling-python/error-handling-fastapi/#creating-custom-exceptions-in-fastapi


#### S3 PRESIGNED URL UPLOAD

https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html