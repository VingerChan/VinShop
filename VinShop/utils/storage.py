from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from VinShop.settings import FDFS_BASE_URL,FDFS_CLIENT_CONF
from fdfs_client.exceptions import DataError


# 迁移能序列化它的开关
@deconstructible
class FastDFSStorage(Storage):
    """上传文件到FastDFS，以返回的file_id作为存储路径"""
    # 决定数据库存什么
    def _save(self, name, content):
        """

        :param name: Django生成的文件名
        :param content: 上传的文件对象
        :return:
        """
        from fdfs_client.client import Fdfs_client
        result = Fdfs_client(FDFS_CLIENT_CONF).upload_by_buffer(content.read())
        if result['Status'] != 'Upload successed.':
            raise RuntimeError('文件上传到FastDFS失败')
        return result['Remote file_id'].decode()
    # 展示图片的生命线
    def url(self, name):
        return FDFS_BASE_URL + name
    def exists(self, name):
        """
            每次上传必走
            存文件:save()->get_available_name()->is_name_available()->exists()
            · 返回True -> Django认为重名，文件名加随机后缀重试
            · 返回False -> 认为空闲，直接进_save()
        """
        return False
    def delete(self,name):
        if not name:
            return
        from fdfs_client.client import Fdfs_client
        try:
            Fdfs_client(FDFS_CLIENT_CONF).delete_file(name)
        # delete_file()内部会抛DataError('Error:2,No such file...')
        # 这里把 文件不存在 当成功处理
        except DataError as e:
            if 'No such file' in str(e):
                raise