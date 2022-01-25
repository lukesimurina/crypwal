from django.db import models
from django.contrib.auth.models import User

class WalletItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField() 
    amount = models.FloatField(default=0)
    
    def __str__(self):
        return self.title