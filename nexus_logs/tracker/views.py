import csv
import datetime as dt
import json

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import ConfigForm, JobEntryForm, ManualEntryForm, UploadTimelineForm
from .models import AppConfig, TimelineEntry
from .parsers import TimelineParseError, parse_timeline

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover - openpyxl is in requirements.txt
    Workbook = None


EXPORT_HEADERS = [
    "Date",
    "Type",
    "Source",
    "Location",
    "Address",
    "Start",
    "End",
    "Duration (min)",
    "Distance (km)",
    "Parts Used",
    "Comments",
]


def _entry_export_row(entry: TimelineEntry) -> list:
    return [
        entry.visit_date.isoformat(),
        entry.get_entry_type_display(),
        entry.get_source_display(),
        entry.location_name,
        entry.address,
        timezone.localtime(entry.start_time).strftime("%Y-%m-%d %H:%M"),
        timezone.localtime(entry.end_time).strftime("%Y-%m-%d %H:%M"),
        entry.duration_minutes,
        entry.distance_km,
        entry.parts_used,
        entry.comments,
    ]


def _parse_date(value, default):
    if not value:
        return default
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return default


def _date_range_from_request(request):
    today = timezone.localdate()
    start_date = _parse_date(request.GET.get("start_date"), today - dt.timedelta(days=today.weekday()))
    end_date = _parse_date(request.GET.get("end_date"), today)
    if end_date < start_date:
        start_date, end_date = end_date, start_date
    return start_date, end_date


def dashboard(request):
    start_date, end_date = _date_range_from_request(request)
    show_home = request.GET.get("show_home") == "1"

    entries = TimelineEntry.objects.filter(visit_date__gte=start_date, visit_date__lte=end_date)

    config = AppConfig.get_solo()
    if config.home_address and not show_home:
        entries = entries.exclude(location_name__icontains=config.home_address).exclude(
            address__icontains=config.home_address
        )

    entries = list(entries.order_by("start_time"))

    days = {}
    for entry in entries:
        days.setdefault(entry.visit_date, []).append(entry)

    day_summaries = []
    for day in sorted(days.keys()):
        day_entries = days[day]
        drives = [e for e in day_entries if e.entry_type == TimelineEntry.DRIVE]
        visits = [e for e in day_entries if e.entry_type == TimelineEntry.VISIT]
        day_summaries.append(
            {
                "date": day,
                "entries": day_entries,
                "visit_count": len(visits),
                "drive_minutes": sum(e.duration_minutes or 0 for e in drives),
                "drive_km": round(sum(e.distance_km or 0 for e in drives), 1),
                "job_forms": {e.pk: JobEntryForm(instance=e) for e in visits},
            }
        )

    context = {
        "day_summaries": day_summaries,
        "start_date": start_date,
        "end_date": end_date,
        "show_home": show_home,
        "config": config,
        "has_entries": bool(entries),
    }
    return render(request, "tracker/dashboard.html", context)


# Fields Google's own data can legitimately refine between exports (e.g. an
# in-progress visit's end_time growing once you've actually left). Never
# includes location_name/address/parts_used/comments — those may have been
# typed in by the user and a re-import must not clobber them.
_REFINABLE_FIELDS = ["end_time", "distance_km", "latitude", "longitude", "raw_data"]


def _identity_key(entry: dict):
    """The stable identity Google reuses for 'the same' visit/drive across
    re-exports. Visits key on their place_id (stable even if start/end get
    refined); drives have no place_id but can't physically overlap for one
    phone, so start_time alone is safe. See the UniqueConstraints on
    TimelineEntry for the DB-level backstop of this same logic."""
    if entry["entry_type"] == TimelineEntry.VISIT:
        return (TimelineEntry.VISIT, entry.get("place_id"), entry["start_time"])
    return (TimelineEntry.DRIVE, None, entry["start_time"])


def _import_parsed_entries(parsed: list) -> tuple:
    """Creates new TimelineEntry rows for segments never seen before, and
    refines already-imported ones in place (see _REFINABLE_FIELDS) instead
    of either duplicating them or leaving stale end times when the same
    Timeline export is re-uploaded — which happens on every import, since
    Google only offers a full-history export, not an incremental one.
    Returns (created_count, updated_count).
    """
    if not parsed:
        return 0, 0

    min_date = min(e["start_time"] for e in parsed).date() - dt.timedelta(days=1)
    max_date = max(e["end_time"] for e in parsed).date() + dt.timedelta(days=1)
    existing = {
        _identity_key(
            {
                "entry_type": e.entry_type,
                "place_id": e.place_id,
                "start_time": e.start_time,
            }
        ): e
        for e in TimelineEntry.objects.filter(
            source=TimelineEntry.GOOGLE, visit_date__gte=min_date, visit_date__lte=max_date
        )
    }

    to_create = []
    to_update = []
    seen_in_batch = set()
    for entry in parsed:
        key = _identity_key(entry)
        if key in seen_in_batch:
            continue  # the export itself repeated this segment
        seen_in_batch.add(key)

        match = existing.get(key)
        if match is None:
            to_create.append(
                TimelineEntry(
                    source=TimelineEntry.GOOGLE,
                    visit_date=entry["start_time"].date(),
                    **entry,
                )
            )
            continue

        changed = False
        for field in _REFINABLE_FIELDS:
            new_value = entry.get(field)
            if new_value is not None and getattr(match, field) != new_value:
                setattr(match, field, new_value)
                changed = True
        if changed:
            to_update.append(match)

    with transaction.atomic():
        created = TimelineEntry.objects.bulk_create(
            to_create, batch_size=500, ignore_conflicts=True
        )
        if to_update:
            TimelineEntry.objects.bulk_update(to_update, _REFINABLE_FIELDS, batch_size=500)

    return len(created), len(to_update)


def upload_timeline(request):
    if request.method == "POST":
        form = UploadTimelineForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = request.FILES["timeline_file"]
            try:
                data = json.load(uploaded)
            except (json.JSONDecodeError, UnicodeDecodeError):
                messages.error(request, "That file isn't valid JSON.")
                return render(request, "tracker/upload.html", {"form": form})

            try:
                parsed = parse_timeline(data)
            except TimelineParseError as exc:
                messages.error(request, str(exc))
                return render(request, "tracker/upload.html", {"form": form})

            created_count, updated_count = _import_parsed_entries(parsed)
            skipped_count = len(parsed) - created_count - updated_count

            messages.success(
                request,
                f"Processed {len(parsed)} timeline segments: "
                f"{created_count} new, {updated_count} refined (e.g. an in-progress "
                f"visit's end time), {skipped_count} unchanged.",
            )
            return redirect(reverse("dashboard"))
    else:
        form = UploadTimelineForm()

    return render(request, "tracker/upload.html", {"form": form})


def edit_entry(request, pk):
    entry = get_object_or_404(TimelineEntry, pk=pk, entry_type=TimelineEntry.VISIT)
    if request.method == "POST":
        form = JobEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, f"Saved job details for {entry.display_name}.")
    return redirect(_back_to_dashboard(request))


def _back_to_dashboard(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    return next_url or reverse("dashboard")


def manual_entry(request):
    if request.method == "POST":
        form = ManualEntryForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            with transaction.atomic():
                visit = TimelineEntry.objects.create(
                    entry_type=TimelineEntry.VISIT,
                    source=TimelineEntry.MANUAL,
                    location_name=cd["location_name"],
                    address=cd["address"],
                    start_time=cd["arrival_time"],
                    end_time=cd["departure_time"],
                    parts_used=cd["parts_used"],
                    comments=cd["comments"],
                )
                if cd["estimated_drive_minutes"]:
                    drive_end = cd["arrival_time"]
                    drive_start = drive_end - dt.timedelta(minutes=cd["estimated_drive_minutes"])
                    TimelineEntry.objects.create(
                        entry_type=TimelineEntry.DRIVE,
                        source=TimelineEntry.MANUAL,
                        location_name="Driving",
                        start_time=drive_start,
                        end_time=drive_end,
                    )
            messages.success(request, f"Added {visit.display_name} to the log.")
            return redirect(f"{reverse('dashboard')}?start_date={visit.visit_date}&end_date={visit.visit_date}")
    else:
        initial = {}
        date_param = request.GET.get("date")
        if date_param:
            initial["arrival_time"] = f"{date_param}T08:00"
            initial["departure_time"] = f"{date_param}T09:00"
        form = ManualEntryForm(initial=initial)

    return render(request, "tracker/manual_entry.html", {"form": form})


def delete_entry(request, pk):
    entry = get_object_or_404(TimelineEntry, pk=pk)
    if request.method == "POST":
        name = entry.display_name if entry.entry_type == TimelineEntry.VISIT else "drive"
        entry.delete()
        messages.success(request, f"Deleted {name}.")
    return redirect(_back_to_dashboard(request))


def export(request):
    start_date, end_date = _date_range_from_request(request)
    config = AppConfig.get_solo()
    fmt = request.GET.get("format") or config.default_export_format

    entries = TimelineEntry.objects.filter(
        visit_date__gte=start_date, visit_date__lte=end_date
    ).order_by("start_time")

    filename = f"nexus-logs_{start_date}_{end_date}.{fmt}"

    if fmt == AppConfig.XLSX:
        if Workbook is None:
            messages.error(request, "openpyxl isn't installed — falling back to CSV.")
            fmt = AppConfig.CSV
        else:
            wb = Workbook()
            ws = wb.active
            ws.title = "Nexus Logs"
            ws.append(EXPORT_HEADERS)
            for entry in entries:
                ws.append(_entry_export_row(entry))
            for column_cells in ws.columns:
                length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
                ws.column_dimensions[column_cells[0].column_letter].width = min(max(length + 2, 10), 50)

            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            wb.save(response)
            return response

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(EXPORT_HEADERS)
    for entry in entries:
        writer.writerow(_entry_export_row(entry))
    return response


def config_view(request):
    config = AppConfig.get_solo()
    if request.method == "POST":
        form = ConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings saved.")
            return redirect(reverse("config"))
    else:
        form = ConfigForm(instance=config)
    return render(request, "tracker/config.html", {"form": form})
