from django import forms

from .models import AppConfig, TimelineEntry

INPUT_CLASSES = "w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-600"


class TailwindStyledForm:
    """Mixin that stamps every field's widget with our standard input
    classes, so templates can just do {{ form.field }} everywhere."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {INPUT_CLASSES}".strip()
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "h-4 w-4"


class UploadTimelineForm(TailwindStyledForm, forms.Form):
    timeline_file = forms.FileField(
        label="Timeline.json / location-history.json",
        help_text="Export from the Google Maps Timeline app on your phone "
        "(Settings → Location → Timeline → Export Timeline data).",
    )


class JobEntryForm(TailwindStyledForm, forms.ModelForm):
    """Used on the dashboard to fill in the job details for a parsed or
    manual visit — also lets the user name/address a visit that Google's
    export only gave coordinates for."""

    class Meta:
        model = TimelineEntry
        fields = ["location_name", "address", "parts_used", "comments"]
        widgets = {
            "location_name": forms.TextInput(
                attrs={"placeholder": "e.g. Villa Lion View, Constantia"}
            ),
            "address": forms.TextInput(attrs={"placeholder": "Street address"}),
            "parts_used": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "One item per line, e.g.\nX1 4x2 plug\nX1 gland\n500mm 16x25 trunking",
                }
            ),
            "comments": forms.Textarea(
                attrs={"rows": 2, "placeholder": "e.g. light breaker tripped"}
            ),
        }


class ManualEntryForm(TailwindStyledForm, forms.Form):
    """'Add Missing Job' — requirement 3b. Creates a visit TimelineEntry
    (source=manual), and optionally a preceding drive entry if a rough
    driving time is supplied."""

    location_name = forms.CharField(max_length=255)
    address = forms.CharField(max_length=500, required=False)
    arrival_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    departure_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    estimated_drive_minutes = forms.IntegerField(
        required=False,
        min_value=0,
        label="Estimated driving time (minutes)",
        help_text="Optional — adds a driving entry immediately before this visit.",
    )
    parts_used = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "One item per line"}),
    )
    comments = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def clean(self):
        cleaned = super().clean()
        arrival = cleaned.get("arrival_time")
        departure = cleaned.get("departure_time")
        if arrival and departure and departure <= arrival:
            raise forms.ValidationError("Departure time must be after arrival time.")
        return cleaned


class ConfigForm(TailwindStyledForm, forms.ModelForm):
    class Meta:
        model = AppConfig
        fields = ["default_export_format", "home_address"]
        widgets = {
            "home_address": forms.TextInput(
                attrs={"placeholder": "e.g. Home (Grande Stellenbosch)"}
            ),
        }
