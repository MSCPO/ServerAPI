import hashlib

from tortoise import Model, fields


class File(Model):
    hash_value = fields.CharField(max_length=64, pk=True)
    file_path = fields.CharField(max_length=255, unique=True)

    @classmethod
    def generate_file_hash(cls, file_content: bytes) -> str:
        """根据文件内容生成哈希值"""
        return hashlib.sha256(file_content).hexdigest()

    class Meta:
        table = "files"
