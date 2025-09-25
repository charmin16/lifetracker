from django.db import models
from django.conf import settings
import datetime
from django.utils.safestring import mark_safe

TRANSACTION_TYPE = (
    ('Credit', 'Credit'),
    ('Withdrawal', 'Withdrawal'),
    ('Transfer', 'Transfer'),
    ('Expense', 'Expense')
)

CATEGORY = (
    ('groceries', 'Groceries (raw food: rice, yam, meat, tomatoes, fruits, etc.'),
    ('eat_out', 'Eating Out / Restaurants'),
    ('fuel', 'Fuel'),
    ('transport', 'Transport'),
    ('airtime/Data', 'Airtime/Data'),
    ('utilities', 'Utilities (Bills)'),
    ('Extd Family', 'Family(Parents, Siblings etc)'),
    ('gifts/Donations', 'Gifts/Donations'),
    ('personal', 'Personal (Haircut, Gym, etc)'),
    ('household', 'Household items/supplies'),
    ('entertainment', 'Entertainment (Alcohol, club, etc)'),
    ('spouse', 'Spouse'),
    ('girl/boyfriend', 'Girlfriend/Boyfriend'),
    ('clothing', 'Clothing'),
    ('education', 'Education'),
    ('vacation', 'Vacation'),
    ('medical', 'Medical/Healthcare'),
    ('child care/family', 'ChildCare/Family Support'),
    ('housing', 'Housing'),
    ('car repair', 'Car Repair/Maintenance'),
    ('savings/Investment', 'Savings/Investment'),
    ('emergency/unexpected', 'Emergency/Unexpected'),
    ('miscellaneous', 'Miscellaneous')
)


class Expense(models.Model):
    date = models.DateField(default=datetime.date.today, blank=True, null=True)
    transaction_type = models.CharField(max_length=100, choices=TRANSACTION_TYPE)
    item_service = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, choices=CATEGORY, blank=True, default="")
    amount = models.PositiveSmallIntegerField()
    note = models.CharField(max_length=200, blank=True, default="")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Idea(models.Model):
    PRIORITY = (
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low')
    )

    STATUS = (
        ('Not Started', 'Not Started'),
        ('In Progress', 'In Progress'),
        ('Done', 'Done')
    )

    CAT = (
        ('Business / Career', 'Business / Career'),
        ('Lifestyle / Personal Growth', 'Lifestyle / Personal Growth'),
        ('Education / Learning', 'Education / Learning'),
        ('Family / Relationships', 'Family / Relationships'),
        ('Intellectual / Creativity', 'Intellectual / Creativity'),
        ('Spirituality / Ethical', 'Spirituality / Ethical')
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    objective = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=100, choices=CAT, default='Business / Career')
    priority = models.CharField(max_length=100, choices=PRIORITY, default='Medium')
    status = models.CharField(max_length=100, choices=STATUS, default='Not Started')
    target_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def formatted_objectives(self):
        if not self.objective:
            return ""
        lines = [line.strip("-• ").strip() for line in self.objective.splitlines() if line.strip()]
        html = "<ul>" + "".join(f"<li>{line}</li>" for line in lines) + "</ul>"
        return mark_safe(html)

    @property
    def progress(self):
        total = self.requirements.count()
        done = self.requirements.filter(is_done=True).count()
        return int((done / total) * 100) if total > 0 else 0

    def update_status(self):
        total = self.requirements.count()
        done = self.requirements.filter(is_done=True).count()
        if done == 0:
            self.status = "Not Started"
        elif done < total:
            self.status = "In Progress"
        else:
            self.status = "Done"
        self.save()

    def save(self, *args, **kwargs):
        # First save the object so it gets a primary key (if new)
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Now it's safe to check related requirements
        if not is_new and self.requirements.exists() and self.progress == 100:
            if self.status != "Done":  # avoid recursive save loop
                self.status = "Done"
                super().save(update_fields=["status"])

    @property
    def remaining_progress(self):
        return 100 - self.progress

    @property
    def progress_offset(self):
        circumference = 188
        return circumference - (circumference * self.progress // 100)

    def __str__(self):
        return self.title


class Requirement(models.Model):
    idea = models.ForeignKey(Idea, related_name='requirements', on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    is_done = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'Done' if self.is_done else 'Pending'})"


