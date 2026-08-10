from django import forms
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )
    name = forms.CharField(label='Nombre completo', max_length=255)
    phone = forms.CharField(label='Teléfono', max_length=20)
    position = forms.CharField(label='Cargo', max_length=255)
    company = forms.CharField(label='Empresa', max_length=255, required=False)
    profession = forms.CharField(label='Profesión', max_length=255, required=False)
    prefer_language = forms.ChoiceField(
        label='Idioma preferido',
        choices=User.Idioma.choices,
        initial=User.Idioma.ES,
    )
    accepted_consent = forms.BooleanField(
        label='Acepto el tratamiento de datos personales',
        required=True,
        error_messages={
            'required': 'Debes aceptar el consentimiento para registrarte.',
        },
    )

    class Meta:
        model = User
        fields = ['email', 'name', 'phone', 'position', 'company', 'profession', 'prefer_language', 'accepted_consent']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = User.Role.VISITANT
        user.accepted_consent = True
        user.consent_date = timezone.now()
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    """AuthenticationForm usa el campo 'username' internamente;
    con USERNAME_FIELD=email, el valor es el correo."""
    username = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )
