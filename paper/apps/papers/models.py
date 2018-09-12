from django.db import models
from apps.users.models import PaperUser
from apps.common.models import TimeStampedModel, HavingAuthorModel
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.utils import timezone

class Paper(TimeStampedModel, HavingAuthorModel):
    title = models.CharField(max_length=50, default="Title")
    content = models.TextField(blank=True, null=True)
    deadline = models.DateTimeField(editable=True, default=None)
    is_deleted = models.BooleanField(default=False)
    is_validated = models.BooleanField(default=False)
    preview_image = models.FileField(upload_to='previews/', default=None)
    preview_image_thumbnail = ImageSpecField(source='preview_image',
                                     processors=[ResizeToFill(380, 250)],
                                     format='JPEG',
                                     options={'quality': 60},
                                     )
    poster_url = models.URLField(null=True)
    only_kaist = models.BooleanField(default=False, null=False)

    @property
    def is_finished(self):
        current = timezone.now()
        diff = self.deadline - current
        if str(diff)[0] == '-':
            return True
        else:
            return False


class Question(models.Model):
    QUESTION_TYPE = (
        ('C', 'Checkbox'),
        ('R', 'Radio'),
        ('O', 'Open-Ended')
    )
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="questions")
    content = models.CharField(max_length=140, default="empty question")
    type = models.CharField(
        max_length=1, choices=QUESTION_TYPE
    )
    is_multiple = models.BooleanField(default=False)

    class Meta:
        order_with_respect_to = 'paper'


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    option = models.CharField(max_length=50, default="option")

    class Meta:
        order_with_respect_to = 'question'
