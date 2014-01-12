import mimetypes, datetime
import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from google.appengine.api.blobstore import create_gs_key
import cloudstorage

__author__ = 'ckopanos@redmob.gr'

import logging

class GoogleCloudStorage(Storage):
    """
    To debug permissions or performance problems replace all occurances of '#logging.' with 'logging.'
    Uncached remote API-calls of cloud services are much slower than traditional file system access calls.
    """

    def __init__(self, location=None, base_url=None):
        if location is None:
            location = settings.GOOGLE_CLOUD_STORAGE_BUCKET
        self.location = location
        if base_url is None:
            base_url = settings.GOOGLE_CLOUD_STORAGE_URL
        self.base_url = base_url
        
    def _open(self, name, mode='rb'):
        """
        Open a file on cloudstorage and immidiately read it completely into memory 
        and return a django.core.files.base.ContentFile (string buffer)
        This is not suitable for huge files.
        """
        filename = self.location+"/"+name
        
        if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
            logging.info("GoogleCloudStorage-open %s", filename)
            
        try:
            # Untested alternative?
            # return cloudstorage.open(filename,mode='r')
            
            gcs_file = cloudstorage.open(filename,mode='r')
            file_d = ContentFile(gcs_file.read())
            gcs_file.close()
            
        except cloudstorage.errors.NotFoundError, e:
            if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
                logging.warning("GoogleCloudStorage-open FILE NOT FOUND %s", name)
            raise IOError('File does not exist: %s' % name)
            
        except cloudstorage.errors.Error, e:
            logging.error(e) # DISPLAY READ PERMISSION & TIMEOUT PROBLEMS
            raise IOError(e)
            
        if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
            logging.info("GoogleCloudStorage-open returned %i bytes.", file_d.size)
            
        return file_d

    def _save(self, name, content):
        filename = self.location+"/"+name
        filename = os.path.normpath(filename)
        
        if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
            logging.info("GoogleCloudStorage-save %s", filename)
        
        type, encoding = mimetypes.guess_type(name)
        #files are stored with public-read permissions. Check out the google acl options if you need to alter this.
        
        try:
            gss_file = cloudstorage.open(filename, mode='w', content_type=type, 
                                options={'x-goog-acl': 'public-read',
                                'cache-control': settings.GOOGLE_CLOUD_STORAGE_DEFAULT_CACHE_CONTROL})
            content.open()
            gss_file.write(content.read())
            content.close()
            gss_file.close()
            
        except cloudstorage.errors.Error, e:
            # import traceback
            # logging.error(traceback.format_exc())
            logging.error(e) # DISPLAY WRITE PERMISSION PROBLEMS
            raise IOError(e)
            
        return name

    def delete(self, name):
        """
        Deletes a file. Does nothing, if file does not exist.
        """
        filename = self.location+"/"+name
        
        if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
            logging.warning("GoogleCloudStorage-delete %s", name)
            
        try:
            cloudstorage.delete(filename)
        except cloudstorage.NotFoundError:
            pass

    def exists(self, name):
        """
        Checks if a file exists. Returns True of False.
        """
        try:
            self._statFile_(name)
            if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
                logging.info("GoogleCloudStorage-exists-yes %s", name)
            return True
            
        except cloudstorage.NotFoundError, e:
            if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
                logging.warning("GoogleCloudStorage-exists-no %s", name)
            return False

    def listdir(self, path=None):
        
        if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
            logging.info("GoogleCloudStorage-listdir %s", path)
            
        directories, files = [], []
        bucketContents = cloudstorage.listbucket(self.location,prefix=path)
        for entry in bucketContents:
            filePath = entry.filename
            head, tail = os.path.split(filePath)
            subPath = os.path.join(self.location,path)
            head = head.replace(subPath,'',1)
            if head == "":
                head = None
            if not head and tail:
                files.append(tail)
            if head:
                if not head.startswith("/"):
                    head = "/"+head
                dirs = head.split("/")[1]
                if not dirs in directories:
                    directories.append(dirs)
                    
        return directories, files

    def size(self, name):
        if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
            logging.info("GoogleCloudStorage-size %s", name)
        stats = self._statFile_(name)
        return stats.st_size

    def accessed_time(self, name):
        """
        raises NotImplementedError
        """
        
        if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
            logging.error("GoogleCloudStorage-ACCESSED NOT IMPLEMENTED %s", name)
            
        raise NotImplementedError

    def created_time(self, name):
        """
        Returns a datetime object containing the creation time of the file. 
        """
        if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
            logging.info("GoogleCloudStorage-created_time %s", name)
            
        try:
            stats = self._statFile_(name)
            return datetime.datetime.fromtimestamp(stats.st_ctime)
        except cloudstorage.NotFoundError:
            raise OSError() # convert to standard filesystem error 

    def modified_time(self, name):
        """
        Returns created datetime. Files cannot be modified on cloud storage.
        """
        return self.created_time(name)

    def url(self, name):
        """
        Returns the public URL to a cloudstorage-website bucket.
        """
        if settings.DEBUG:
            # we need this in order to display images, links to files, etc from the local appengine server
            filename = "/gs"+self.location+"/"+name
            key = create_gs_key(filename)
            hostport = settings.get('GOOGLE_CLOUD_STORAGE_SDK_HOST', 'localhost:8000')
            url = "http://"+hostport+"/blobstore/blob/"+key+"?display=inline"

        url = self.base_url+"/"+name
        
        if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
            logging.info("GoogleCloudStorage-url %s", url)
            
        return url

    def _statFile_(self, name):
        """
        Primitive, private method. Returns a Google Stat object, raises cloudstorage.NotFoundError
        """
        filename = self.location+"/"+name
        
        if settings.GOOGLE_CLOUD_STORAGE_LOGGING:
            logging.info("GoogleCloudStorage-stat %s", filename)
            
        return cloudstorage.stat(filename)