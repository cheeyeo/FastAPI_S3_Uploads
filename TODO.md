### TODO

* Dockerzie the application

* Support multiple uploads in UI

* Uploads to resume even with page refresh ; requires additional UI component and endpoint

* Add / use celery for the upload progress ?
    https://celery.school/celery-progress-bars-with-fastapi-htmx
    https://github.com/bstiel/celery-task-progress-bar


* CRUD for the uploads


https://github.com/nicholasadamou/s3-large-file-uploader/tree/master/backend

```
import boto3
import requests

s3 = boto3.client('s3')
max_size = 5 * 1024 * 1024 #you can define your own size

res = s3.create_multipart_upload(Bucket=bucket_name, Key=key)
upload_id = res['UploadId']

# please note this is for only 1 part of the file, you have to do it for all parts and store all the etag, partnumber in a list 

parts=[]
signed_url = s3.generate_presigned_url(ClientMethod='upload_part',Params={'Bucket': bucket_name, 'Key': key, 'UploadId': upload_id, 'PartNumber': part_no})

with target_file.open('rb') as f:
      file_data = f.read(max_size) #here reading content of only 1 part of file 

res = requests.put(signed_url, data=file_data)

etag = res.headers['ETag']
parts.append({'ETag': etag, 'PartNumber': part}) #you have to append etag and partnumber of each parts  

#After completing for all parts, you will use complete_multipart_upload api which requires that parts list 
res = s3.complete_multipart_upload(Bucket=bucket_name, Key=key, MultipartUpload={'Parts': parts},UploadId=upload_id)

```

To create ClientError in boto3 for testing:
```
        raise ClientError(operation_name="S3 PUT", error_response={
            "Error": {"Message": "ERROR WITH S3 UPLOAD", "Code": "123"}})
```