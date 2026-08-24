from django.core.management import BaseCommand
from utils.generate_static_detail import static_sku_detail,static_all_sku_detail

class Command(BaseCommand):
    help = '商品详情页静态化'
    def add_arguments(self, parser):
        parser.add_argument('--sku_id',type=int,help='指定SKU ID，不指定则全量生成')
    def handle(self, *args, **options):
        sku_id = options.get('sku_id')
        if sku_id:
            static_sku_detail(sku_id)
            self.stdout.write(self.style.SUCCESS(f"SKU {sku_id} 静态化完成"))
        else:
            static_all_sku_detail()
            self.stdout.write(self.style.SUCCESS('全量静态化完成'))