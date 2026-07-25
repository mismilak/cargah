from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

User = get_user_model()


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='ایمیل',
        help_text='مثال: example@mail.com'
    )
    first_name = forms.CharField(
        required=True,
        label='نام',
        help_text='نام را به فارسی وارد کنید'
    )
    last_name = forms.CharField(
        required=True,
        label='نام خانوادگی',
        help_text='نام خانوادگی را به فارسی وارد کنید'
    )
    phone = forms.CharField(
        required=True,
        label='شماره موبایل',
        help_text='مثال: 09123456789',

    )
    password1 = forms.CharField(
        required=True,
        label='رمز عبور',
        help_text='رمز عبور باید حداقل ۸ کاراکتر باشد و خیلی ساده نباشد',
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        required=True,
        label='تکرار رمز عبور',
        help_text='رمز عبور را دوباره وارد کنید',
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields.pop('username', None)

        self.fields['email'].widget.attrs.update({
            'placeholder': 'example@mail.com'
        })
        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'نام'
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'نام خانوادگی'
        })
        self.fields['phone'].widget.attrs.update({
            'placeholder': '09123456789', 'type': 'number'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'رمز عبور'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'تکرار رمز عبور'
        })

        self.fields['email'].help_text = 'مثال: example@mail.com'
        self.fields['first_name'].help_text = 'نام را به فارسی وارد کنید'
        self.fields['last_name'].help_text = 'نام خانوادگی را به فارسی وارد کنید'
        self.fields['phone'].help_text = 'مثال: 09123456789'
        self.fields['password1'].help_text = 'رمز عبور باید حداقل ۸ کاراکتر باشد و خیلی ساده نباشد'
        self.fields['password2'].help_text = 'رمز عبور را دوباره وارد کنید'

        self.order_fields([
            'email',
            'first_name',
            'last_name',
            'phone',
            'password1',
            'password2',
        ])

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('این ایمیل قبلاً ثبت شده است.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        required=True,
        label='ایمیل',
        help_text='مثال: example@mail.com'
    )
    password = forms.CharField(
        required=True,
        label='رمز عبور',
        help_text='رمز عبور را وارد کنید',
        widget=forms.PasswordInput

    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': 'example@mail.com'
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': 'رمز عبور'
        })

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(
                self.request,
                username=email,
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError('ایمیل یا رمز عبور نادرست است.')
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
