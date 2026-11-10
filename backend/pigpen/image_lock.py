"""Serialize immutable-image publication, backup and retention across processes."""
from contextlib import contextmanager
import fcntl, os

@contextmanager
def image_lock(settings):
    settings.verify_storage()
    fd=os.open(settings.data_dir/'.images.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)
