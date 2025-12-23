from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0002_update_status_choices"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="status",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("active", "Active"),
                    ("inactive", "Inactive"),
                    ("pending", "Pending"),
                ],
                default="pending",
            ),
        ),
    ]
