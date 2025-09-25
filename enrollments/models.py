# enrollments/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Enrollment(models.Model):
    # 열거형(status 필드에 사용됨)
    class Status(models.TextChoices):
        NOT_TAKEN = "NOT_TAKEN", "미수강"
        ENROLLED  = "ENROLLED", "수강중"
        COMPLETED = "COMPLETED", "수료"

    id = models.BigAutoField(primary_key=True)
    employee = models.ForeignKey("organizations.Employee", on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NOT_TAKEN, db_index=True)
    completion_rate = models.PositiveSmallIntegerField(default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    last_session_at = models.DateTimeField(null=True, blank=True)
