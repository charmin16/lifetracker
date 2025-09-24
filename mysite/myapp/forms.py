# forms.py
from django import forms
from .models import Idea

class IdeaForm(forms.ModelForm):
    # free-form textarea for entering requirements (one-per-line) at creation time
    requirements_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "- a three bedroom apartment\n- seven sewing machines for a start"
        }),
        label="Requirements (one per line)"
    )

    class Meta:
        model = Idea
        # show only model fields we want on create/edit; requirements handled separately
        fields = ["title", "objective", "category", "priority", "status", "target_date"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "eg setup a fashion school"
            }),
            "objective": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "- make beautifully crafted dresses for clients\n- fashion school"
            }),
            "category": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "target_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }
