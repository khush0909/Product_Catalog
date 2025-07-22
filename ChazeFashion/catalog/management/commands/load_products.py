# catalog/management/commands/load_products.py

import csv
from django.core.management.base import BaseCommand
from catalog.models import Product

class Command(BaseCommand):
    help = 'Load products from CSV'

    def handle(self, *args, **kwargs):
        with open('C:\\Users\\V\\OneDrive\\Desktop\\PEP CLASSES 4\\clothing_products.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Product.objects.create(

                    pr_name=row['name'],
                    pr_brand=row['description'],
                    pr_price=row['price'],
                    pr_cate=row['category'],
                    pr_season=row['season'],
                    pr_fabric=row['fabric'],
                    pr_stk_quant=row['stock_quantity'],
                )
        self.stdout.write(self.style.SUCCESS("✅ Successfully loaded products"))
