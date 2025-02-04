from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Employee, Attendance, Salary
from django import forms

from datetime import datetime, date
import calendar


# 認証関連ビュー
class AttendanceListView(ListView):
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendance'
    paginate_by = 10
    
    def get_queryset(self):
        # 未ログインの場合は空のクエリセットを返す
        if not self.request.user.is_authenticated:
            return Attendance.objects.none()
        # 一般ユーザーは自分の記録のみ表示
        if not self.request.user.is_staff:
            return Attendance.objects.filter(employee=self.request.user)
        return Attendance.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ログイン状態をテンプレートに渡す
        context['is_authenticated'] = self.request.user.is_authenticated
        if self.request.user.is_authenticated:
            context['user_info'] = {
                'username': self.request.user.username,
                'employee_id': self.request.user.employee_id,
                'hourly_rate': int(self.request.user.hourly_rate),
            }
        return context

class AttendanceCreateView(CreateView):
    model = Attendance
    template_name = 'attendance/attendance_form.html'
    fields = ['date', 'start_time', 'end_time', 'break_time', 'notes']
    success_url = reverse_lazy('attendance:attendance_list')

    def get_initial(self):
        initial = super().get_initial()
        # URLパラメータから選択された日付を取得
        selected_date = self.request.GET.get('selected_date')
        if selected_date:
            initial['date'] = selected_date
        else:
            initial['date'] = datetime.now().strftime('%Y-%m-%d')
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # 日付フィールドの設定
        initial_date = self.get_initial().get('date')
        form.fields['date'].widget = forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'value': initial_date
            }
        )
        # 開始時間フィールドの設定
        form.fields['start_time'].widget = forms.TimeInput(
            attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '09:00',
                'min': '00:00',
                'max': '23:00',
                'step': '900'
            }
        )
        # 終了時間フィールドの設定
        form.fields['end_time'].widget = forms.TimeInput(
            attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '17:30',
                'min': '00:00',
                'max': '23:00',
                'step': '900'
            }
        )
        # 休憩時間フィールドの設定
        form.fields['break_time'].widget = forms.Select(
            choices=[
                (0, '0分'),
                (30, '30分'),
                (45, '45分'),
                (60, '60分'),
                (75, '75分'),
                (90, '90分'),
                (120, '120分')
            ],
            attrs={'class': 'form-control'}
        )
        # 備考フィールドの設定
        form.fields['notes'].widget = forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '備考があれば入力してください'
            }
        )
        return form

    def form_valid(self, form):
        # 同じ日の勤怠記録が既に存在するかチェック
        existing_attendance = Attendance.objects.filter(
            employee=self.request.user,
            date=form.cleaned_data['date']
        ).first()

        if existing_attendance:
            form.add_error('date', '指定された日付の勤怠記録は既に存在します。')
            return self.form_invalid(form)

        form.instance.employee = self.request.user
        return super().form_valid(form)

# 勤怠登録一覧
class AttendanceCreateListView(ListView):
    model = Attendance
    template_name = 'attendance/attendance_create_list.html'
    context_object_name = 'attendance'
    paginate_by = 31

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 現在の年月を取得
        current_date = datetime.now()
        year = int(self.request.GET.get('year', current_date.year))
        month = int(self.request.GET.get('month', current_date.month))

        # 月が12を超えた場合、年を1増やして月を1に
        if month > 12:
            year += 1
            month = 1
        # 月が1未満の場合、年を1減らして月を12に
        elif month < 1:
            year -= 1
            month = 12
    
        # 指定した月の日数を取得
        _, last_day = calendar.monthrange(year, month)

        # 月の全日付のリストを作成
        date_list = []
        for day in range(1, last_day + 1):
            current_date = date(year, month, day)

            attendance = Attendance.objects.filter(
                employee=self.request.user,
                date=current_date
            ).first()
            
            date_list.append({
                'date': current_date,
                'attendance': attendance,
            })

        # 合計勤務時間を計算
        total_working_hours = 0
        for date_item in date_list:
            if date_item['attendance'] and date_item['attendance'].working_hours:
                total_working_hours += date_item['attendance'].working_hours

        context['date_list'] = date_list
        context['year'] = year
        context['month'] = month
        context['total_working_hours'] = round(total_working_hours, 1)
        return context

# 給与関連
class SalaryListView(ListView):
    model = Salary
    template_name = 'attendance/salary_list.html'
    context_object_name = 'salaries'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 現在の年月を取得
        current_date = datetime.now()
        year = int(self.request.GET.get('year', current_date.year))
        month = int(self.request.GET.get('month', current_date.month))

        # 月が12を超えた場合、年を1増やして月を1に
        if month > 12:
            year += 1
            month = 1
        # 月が1未満の場合、年を1減らして月を12に
        elif month < 1:
            year -= 1
            month = 12

        # 指定月の勤怠記録を取得
        attendances = Attendance.objects.filter(
            employee=self.request.user,
            date__year=year,
            date__month=month
        )

        # 合計勤務時間を計算
        total_working_hours = 0
        for attendance in attendances:
            if attendance.working_hours:
                total_working_hours += attendance.working_hours

        # 給与計算
        hourly_rate = self.request.user.hourly_rate
        total_salary = total_working_hours * float(hourly_rate)

        context.update({
            'year': year,
            'month': month,
            'total_working_hours': round(total_working_hours, 1),
            'hourly_rate': int(hourly_rate),
            'total_salary': int(total_salary),
        })
        return context

# ログイン、ログアウト
class LoginView(LoginView):
    template_name = 'attendance/login.html'
    redirect_authenticated_user = True
    LOGIN_REDIRECT_URL = 'attendance:attendance_list'
    next_page = 'attendance:attendance_list'

class LogoutView(LogoutView):
    template_name = 'attendance/logout.html'
    next_page = 'login'

# 新規登録
class UserCreateView(CreateView):
    model = Employee
    template_name = 'attendance/user_form.html'
    fields = ['username', 'password', 'employee_id', 'hourly_rate']
    success_url = reverse_lazy('attendance:login')

    def form_valid(self, form):
        """パスワードをハッシュ化して保存"""
        password = form.cleaned_data['password']
        form.instance.set_password(password)
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        """パスワードをハッシュ化して表示"""
        form = super().get_form(form_class)
        form.fields['password'].widget = forms.PasswordInput()
        return form

# 勤怠記録更新
class AttendanceUpdateView(UpdateView):
    model = Attendance
    template_name = 'attendance/attendance_form.html'
    fields = ['date', 'start_time', 'end_time', 'break_time', 'notes']
    success_url = reverse_lazy('attendance:attendance_create_list')

    def get_queryset(self):
        return Attendance.objects.filter(employee=self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # 日付フィールドの設定
        form.fields['date'].widget = forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        )
        # 開始時間フィールドの設定
        form.fields['start_time'].widget = forms.TimeInput(
            attrs={
                'type': 'time',
                'class': 'form-control',
                'min': '00:00',
                'max': '23:00',
                'step': '900'
            }
        )
        # 終了時間フィールドの設定
        form.fields['end_time'].widget = forms.TimeInput(
            attrs={
                'type': 'time',
                'class': 'form-control',
                'min': '00:00',
                'max': '23:00',
                'step': '900'
            }
        )
        # 休憩時間フィールドの設定
        form.fields['break_time'].widget = forms.Select(
            choices=[
                (0, '0分'),
                (30, '30分'),
                (45, '45分'),
                (60, '60分'),
                (75, '75分'),
                (90, '90分'),
                (120, '120分')
            ],
            attrs={'class': 'form-control'}
        )
        # 備考フィールドの設定
        form.fields['notes'].widget = forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3
            }
        )
        return form

# ユーザー情報編集    
class UserUpdateView(UpdateView):
    model = Employee
    template_name = 'attendance/user_form.html'
    fields = ['username', 'employee_id', 'hourly_rate']
    success_url = reverse_lazy('attendance:attendance_list')

    def get_object(self):
        return self.request.user
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        return form
    
# パスワードの変更
class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'attendance/password_change_form.html'
    success_url = reverse_lazy('attendance:attendance_list')

    def form_valid(self, form):
        messages.success(self.request, 'パスワードを変更しました。')
        return super().form_valid(form)
