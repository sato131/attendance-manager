from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone

class Employee(AbstractUser):
    """従業員モデル"""

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='employee_set'
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='employee_set'
    )
    employee_id = models.CharField('名前', max_length=10, unique=True)
    hourly_rate = models.DecimalField('時給', max_digits=10, decimal_places=2, default=1000)

    class Meta:
        verbose_name = '名前'
        verbose_name_plural = 'ユーザ一覧'

    def get_absolute_url(self):
        """詳細ページのURLを返す"""
        return reverse('employee_detail', kwargs={'pk': self.pk})
    
class Attendance(models.Model):
    """勤怠記録モデル"""

    employee = models.ForeignKey(Employee, verbose_name='名前', 
                                 on_delete=models.CASCADE, 
                                 related_name='attendances')
    date = models.DateField('日付', default=timezone.now)
    start_time = models.TimeField('開始時間', default='08:00:00')
    end_time = models.TimeField('終了時間', default='17:00:00', null=True, blank=True)
    break_time = models.DurationField('休憩時間', default='01:00:00')
    notes = models.TextField('備考', blank=True)

    class Meta:
        verbose_name = '勤怠記録'
        verbose_name_plural = '勤怠記録一覧'
        unique_together = ('employee', 'date')
        ordering = ['date', 'start_time']

    def get_absolute_url(self):
        return reverse('attendance_detail', kwargs={'pk': self.pk})
    
    @property
    def working_hours(self):
        """実労働時間を計算(休憩時間を除く)"""
        if not self.end_time:
            return None
        
        # 労働時間の計算（時間を分に変換して計算）
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        
        # 総勤務時間（分）= 終了時間 - 開始時間
        # 例: 17:15 (1035分) - 8:45 (525分) = 510分 (8.5時間)
        total_minutes = end_minutes - start_minutes
        
        # 休憩時間（分）を取得
        break_minutes = 60  # 1時間 = 60分
        
        # 実労働時間（休憩時間を引く）
        # 例: 510分 - 60分 = 450分 (7.5時間)
        working_minutes = total_minutes - break_minutes
        
        # 時間に変換（小数点第1位まで）
        # 450分 ÷ 60 = 7.5時間
        working_hours = working_minutes / 60
        
        return round(working_hours, 1)
    
class Salary(models.Model):
    """給与計算モデル"""

    employee = models.ForeignKey(
        Employee, 
        verbose_name='名前', 
        on_delete=models.CASCADE,
        related_name='salaries')
    period_start = models.DateField('計算期間開始')
    period_end = models.DateField('計算期間終了')
    regular_hours = models.DecimalField(
        '通常勤務時間', 
        max_digits=10, decimal_places=2)
    overtime_hours = models.DecimalField(
        '残業時間',
        max_digits=10,
        decimal_places=2)
    total_amount = models.DecimalField(
        '給与合計',
        max_digits=10,
        decimal_places=2)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    class Meta:
        verbose_name = '給与'
        verbose_name_plural = '給与一覧'
        ordering = ['-period_start']