import uuid
from django.db import models
from common.models import TimeStampedModel

class Course(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField("교육 코드", max_length=30, unique=True)
    title = models.CharField("교육명", max_length=200)
    description = models.TextField("교육 설명", blank=True)
    duration_min = models.PositiveIntegerField("권장 소요시간(분)", default=0)

    class Meta:
        indexes = [models.Index(fields=["code"]), models.Index(fields=["title"])]
        verbose_name = "교육"
        verbose_name_plural = "교육"

    def __str__(self):
        return f"[{self.code}] {self.title}"
