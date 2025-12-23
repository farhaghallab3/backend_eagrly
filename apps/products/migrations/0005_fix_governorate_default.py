# Generated manually to fix governorate default

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_product_governorate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='governorate',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
