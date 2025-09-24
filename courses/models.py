import uuid
from django.db import models
from common.models import TimeStampedModel

# MotionType에 대한 코스 정보
class Course(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # 동작 평가 기능과 연결함
    # 예를 들어 "소화기 사용법" 이라는 교육에 소화기 들기
    motion_type = models.ForeignKey("ai.MotionType", on_delete=models.CASCADE, null=True)
    code = models.CharField("교육 코드", max_length=30, unique=True)
    title = models.CharField("교육명", max_length=200)
    description = models.TextField("교육 설명", blank=True)
    duration_min = models.PositiveIntegerField("권장 소요시간(분)", default=0)

    class Meta:
        # code와 title 필드에 대한 인덱스 생성(조회 관련)
        indexes = [models.Index(fields=["code"]), models.Index(fields=["title"])]
        verbose_name = "교육"
        verbose_name_plural = "교육"

    def __str__(self):
        return f"[{self.code}] {self.title}"
