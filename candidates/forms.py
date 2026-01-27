from django import forms
from .models import Candidate


class CandidateForm(forms.ModelForm):
    """Form to edit candidate details."""
    class Meta:
        model = Candidate
        fields = ['name', 'email', 'phone', 'age', 'experience_years', 'previous_experience']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'previous_experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '{"Company": "Position"}'}),
        }
        help_texts = {
            'previous_experience': 'Enter valid JSON format only. Example: {"Google": "Engineer"}',
        }


class ExcelUploadForm(forms.Form):
    file = forms.FileField(label='Select Excel File (.xlsx)')

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith('.xlsx'):
            raise forms.ValidationError("Only .xlsx files are allowed.")
        return file

class ScheduleForm(forms.Form):
    interview_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label="Interview Date & Time"
    )
    # Range Input (e.g. 2-10)
    range_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1-10'}),
        label="Select by ID Range"
    )