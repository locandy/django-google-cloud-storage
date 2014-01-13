django-google-cloud-storage
===========================

A file storage backend for django appengine projects that uses google cloud storage

If you run your projects on Google's appengine and you are using the django framework you might need this
file backend since there is no way to upload files, images, etc on appengine. Although solutions exist for
the amazon cloud storage i have not found a file backend for google cloud storage. This backend does work
with google cloud storage, although in early development. I have used it with regular file uploads and with
file manager solutions such as django-filer. The code as it is right now stores files for public use (i.e. a web site's images)

Prerequisites
-------------

You need to have an appengine project. This will not work as a standalone solution for non appengine django
projects, since there is no authentication mechanism with the google cloud storage implemented.

You need to download the GCS client library from
https://developers.google.com/appengine/docs/python/googlecloudstorageclient/download
unzip the file and copy the cloudstorage folder, found in the src folder, and install in in your project directory.

Installation
-------------

  1. Install cloudstorage by copying it to your appengine app root directory (where the app.yaml resides). https://code.google.com/p/appengine-gcs-client/downloads/list
  1. Copy the googleCloud.py your appengine app root directory (where the app.yaml resides).
  1. After successful config disable the logging in the googleCloud.py file by commenting out all logging

Configuration
-------------

On your django settings.py file you need to add the following settings

    GOOGLE_CLOUD_STORAGE_BUCKET = '/your_bucket_name' # the name of the bucket you have created from the google cloud storage console
    GOOGLE_CLOUD_STORAGE_URL = 'http://storage.googleapis.com/bucket' #whatever the ulr for accessing your cloud storgage bucket
    GOOGLE_CLOUD_STORAGE_DEFAULT_CACHE_CONTROL = 'public, max-age: 7200' # default cache control headers for your files
    # optional: GOOGLE_CLOUD_STORAGE_SDK_HOST = 'localhost:8000' # serve local urls
    GOOGLE_CLOUD_STORAGE_LOGGING = True # log every access for profiling or debugging
    
And finally declare the file storage backend you will use on your settings.py file

    DEFAULT_FILE_STORAGE = 'googleCloud.GoogleCloudStorage'
    
IMPORTANT NOTES
---------------

Cloud storage is about 1000 times slower than file access because every request 
will be a remote procedure call. Be sure to use a cloud compatible django based software.
To allow easy configuration and profiling in error-message hostile environments 
(e.g. django-CMS) every single request is logged when GOOGLE_CLOUD_STORAGE_LOGGING = True.

Known performance:
  * django-CMS (6-7 seconds per request because of easy-thumbnails's unoptimized file accesses on every request): https://github.com/SmileyChris/easy-thumbnails/issues/283



