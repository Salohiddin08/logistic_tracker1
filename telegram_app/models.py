from django.db import models


class TelegramSession(models.Model):
    api_id = models.BigIntegerField()
    api_hash = models.CharField(max_length=255)
    string_session = models.TextField()

    def __str__(self):
        return f"Session {self.id}"


class Channel(models.Model):
    channel_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    is_tracked = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.channel_id})"


class Message(models.Model):
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE)
    message_id = models.BigIntegerField()
    sender_id = models.BigIntegerField(null=True, blank=True)
    sender_name = models.CharField(max_length=255, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('channel', 'message_id')


# Xom xabarlarni alohida jadvalda saqlash (oldingi loyiha uchun)
class TelegramMessage(models.Model):
    message_id = models.BigIntegerField()
    text = models.TextField()
    date = models.DateTimeField()
    user_id = models.BigIntegerField()
    channel_id = models.BigIntegerField()
    location_uz = models.CharField(max_length=255, null=True, blank=True)
    location_ru = models.CharField(max_length=255, null=True, blank=True)
    location_en = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.channel_id}-{self.message_id}"


# Yuk eʼlonlaridan parsed maʼlumotlar
class Shipment(models.Model):
    message = models.ForeignKey('Message', on_delete=models.CASCADE, related_name='shipment')
    origin = models.CharField(max_length=255, null=True, blank=True)
    destination = models.CharField(max_length=255, null=True, blank=True)
    cargo_type = models.CharField(max_length=255, null=True, blank=True)
    truck_type = models.CharField(max_length=100, null=True, blank=True)
    payment_type = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        if self.origin or self.destination:
            return f"{self.origin} → {self.destination} ({self.phone})"
        return f"Shipment for message {self.message.message_id}"
