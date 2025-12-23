from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="status",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("active", "Active"),
                    ("sold", "Sold"),
                    ("inactive", "Inactive"),
                ],
                default="inactive",
            ),
        ),
    ]
