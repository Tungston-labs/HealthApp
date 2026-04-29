from django.db import models

class Plan(models.Model):
    PLAN_TYPES = (
        ("3_days", "3 Days"),
        ("6_days", "6 Days"),
    )

    plan_name = models.CharField(max_length=200)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    single_price = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    couple_price = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    group_price = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    description = models.TextField()
    upload_file = models.ImageField(upload_to="plans/images/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.plan_name
