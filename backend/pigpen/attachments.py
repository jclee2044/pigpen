from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
import os
import tempfile
import warnings
from PIL import Image, UnidentifiedImageError
from . import schema as s
from .records import get, expect
from .errors import DomainError

MAX_UPLOAD=10*1024*1024
IMAGE_TYPES={'PNG':('image/png','.png'),'JPEG':('image/jpeg','.jpg'),'WEBP':('image/webp','.webp')}


def validate_image(data,claimed_type):
    if not data or len(data)>MAX_UPLOAD:
        raise DomainError('image_size','Upload an image up to 10 MiB',413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                if image.format not in IMAGE_TYPES or image.width*image.height>25_000_000:
                    raise ValueError()
                media,extension=IMAGE_TYPES[image.format]
                if claimed_type != media:
                    raise ValueError()
                image.verify()
            with Image.open(BytesIO(data)) as image:
                image.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise DomainError('image_format','Upload a valid JPEG, PNG or WebP image matching its media type') from None
    return media,extension


def image_metadata(data, media_type, filename):
    media,extension=validate_image(data,media_type)
    digest=sha256(data).hexdigest()
    filename=Path((filename or 'image').replace('\\','/')).name
    filename=''.join(x for x in filename if x.isprintable())[:200] or 'image'+extension
    return dict(storage_key=digest+extension,filename=filename,media_type=media,byte_size=len(data),checksum=digest)


def store_image(settings,data,media_type,filename):
    media,extension=validate_image(data,media_type)
    digest=sha256(data).hexdigest();key=digest+extension
    settings.uploads_dir.mkdir(mode=0o700,parents=True,exist_ok=True)
    path=settings.uploads_dir/key
    # Publish only a complete, flushed immutable object. A crash during upload
    # can leave a temporary file, never a partial object at the final digest path.
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=settings.uploads_dir,prefix='.upload-',delete=False) as output:
            temporary=Path(output.name)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(temporary,path)
        except FileExistsError:
            if path.is_symlink() or sha256(path.read_bytes()).hexdigest()!=digest:
                raise DomainError('storage','Stored attachment failed its integrity check',503)
        directory=os.open(settings.uploads_dir,os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    filename=Path((filename or 'image').replace('\\','/')).name
    filename=''.join(x for x in filename if x.isprintable())[:200] or 'image'+extension
    return dict(storage_key=key,filename=filename,media_type=media,byte_size=len(data),checksum=digest)


def attachment_path(settings,record):
    key=record['storage_key']
    if not re.fullmatch(r'[0-9a-f]{64}\.(png|jpg|webp)',key):
        raise DomainError('storage','Invalid attachment storage key',503)
    path=settings.uploads_dir/key
    if path.is_symlink() or not path.is_file():
        raise DomainError('storage','Attachment file unavailable',503)
    return path


class AttachmentServices:
    def do_attachment_create(self,c,op):
        data=op['data'];get(c,s.purchases,data['purchase_id'])
        path=attachment_path(self.db.settings,data)
        if path.stat().st_size!=data['byte_size'] or sha256(path.read_bytes()).hexdigest()!=data['checksum']:
            raise DomainError('storage','Attachment failed its integrity check',503)
        return self.save(c,s.attachments,dict(id=op['entity_id'],uploader_id=op['actor_id'],**data))

    def do_attachment_delete(self,c,op):
        row=get(c,s.attachments,op['entity_id']);expect(row,op['data']['expected_revision'])
        # Immutable objects are retained for consistent backups; cleanup is a separate policy.
        return self.save(c,s.attachments,{'deleted':True},row)
