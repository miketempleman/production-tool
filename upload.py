import boto3
import botocore

import threading
import os
import sys


class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()


def upload():
    s3 = boto3.resource('s3')

    targetpath = os.path.expanduser('~/git/plover/plover/target/plover-1.00.war')
    print("Upload app server war at %s to object 'plover-upload.war' in the s3 plover bucket ", targetpath)
    s3.Object('plover', 'plover-upload.war').upload_file(targetpath, Callback=ProgressPercentage(targetpath))
    print("\nCompleted uploading " + targetpath + " to plover-upload.war in bucket 'plover' ")

def rename():
    s3 = boto3.resource('s3')
    print ("Renaming upload temporary to plover.war")
    try:
        result = s3.Object('plover','plover.war').copy_from(CopySource='plover/plover-upload.war')
        s3.Object('plover','plover-upload.war').delete()
        print("Upload complete")
    except botocore.exceptions.ClientError as e:
        print(e)
        print("Rename war stopped. Verify that plover-upload.war is in bucket plover")
        raise botocore.exceptions.ClientError('Processing stopped')