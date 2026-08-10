from django import forms

from .models import Customer


class ReceptionForm(forms.Form):
    customer_id = forms.IntegerField(widget=forms.HiddenInput)
    description = forms.CharField(widget=forms.Textarea, required=False)
    count_request = forms.IntegerField(min_value=1, initial=1, required=True)



class CustomerCreateForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'customer_workshop_name', 'phone', 'is_legal']


from .models import ServiceType


class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = ['name', 'machine_name', 'unit', 'base_price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'machine_name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }
