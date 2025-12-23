# Generated manually for making buyer/seller non-nullable

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0004_remove_chat_participants_alter_chat_buyer_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='buyer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_chats', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='chat',
            name='seller',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_chats', to=settings.AUTH_USER_MODEL),
        ),
    ]
