from typing import Optional

from django.db import models


class TimelineEntry(models.Model):
    """
    One row on the daily timeline.

    Two kinds of row share this table so the dashboard can render a single
    chronologically-ordered list, exactly like the Google Timeline UI does:
      - "visit"  -> time spent at a place (job site, home, etc.)
      - "drive"  -> travel between two visits

    Each row also knows whether it came from a parsed Timeline.json
    ("google") or was typed in by hand via "Add Missing Job" ("manual"),
    since the phone's GPS/battery isn't always reliable.
    """

    VISIT = "visit"
    DRIVE = "drive"
    ENTRY_TYPE_CHOICES = [
        (VISIT, "Visit"),
        (DRIVE, "Drive"),
    ]

    GOOGLE = "google"
    MANUAL = "manual"
    SOURCE_CHOICES = [
        (GOOGLE, "Google Timeline"),
        (MANUAL, "Manual Entry"),
    ]

    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=MANUAL)

    # visit fields
    location_name = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=500, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    # Google's own place identifier — stable across re-exports even when
    # start/end times get refined, so it's the real de-dupe key for visits
    # (see tracker.parsers and the re-import logic in tracker.views).
    place_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    # drive fields
    distance_km = models.FloatField(null=True, blank=True)

    # shared timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    # Denormalised for cheap date-range filtering on the dashboard.
    visit_date = models.DateField(db_index=True)

    # job data (requirement 3) — only meaningful on visit rows, but kept on
    # the same row so saving/exporting a job never needs a second lookup.
    parts_used = models.TextField(blank=True)
    comments = models.TextField(blank=True)

    # original parsed segment, kept for troubleshooting bad imports
    raw_data = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]
        indexes = [models.Index(fields=["visit_date", "start_time"])]
        constraints = [
            # A visit's own place_id + start_time is its stable identity
            # across re-exports — end_time often gets extended on a later
            # export if the visit was still ongoing when the previous
            # export was taken. Matching on the full window (start AND end)
            # would treat that refined visit as a brand-new one instead of
            # updating it, letting a duplicate slip in on every re-import.
            models.UniqueConstraint(
                fields=["source", "place_id", "start_time"],
                condition=models.Q(entry_type="visit"),
                name="unique_visit_per_place_start",
            ),
            # Drives have no place_id, but two drives can't genuinely start
            # at the same instant for one phone, so start_time alone is a
            # safe identity here.
            models.UniqueConstraint(
                fields=["source", "start_time"],
                condition=models.Q(entry_type="drive"),
                name="unique_drive_per_start",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.start_time and not self.visit_date:
            self.visit_date = self.start_time.date()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        if self.entry_type == self.DRIVE:
            return f"Drive {self.start_time:%H:%M}-{self.end_time:%H:%M} ({self.distance_km or '?'} km)"
        return f"{self.location_name or self.address} {self.start_time:%H:%M}-{self.end_time:%H:%M}"

    @property
    def duration_minutes(self) -> Optional[int]:
        if not self.start_time or not self.end_time:
            return None
        return round((self.end_time - self.start_time).total_seconds() / 60)

    @property
    def parts_list(self):
        """Parts textarea, one per line -> list, for template bullet rendering."""
        return [line.strip() for line in self.parts_used.splitlines() if line.strip()]

    @property
    def maps_link(self) -> Optional[str]:
        """Deep link built from this visit's own coordinates — useful since
        Timeline exports rarely include a human-readable place name."""
        if self.latitude is None or self.longitude is None:
            return None
        return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"

    @property
    def display_name(self) -> str:
        return self.location_name or self.address or "Unnamed location"


class AppConfig(models.Model):
    """
    Singleton settings row (requirement 5). Always accessed via
    AppConfig.get_solo() so callers never have to think about the pk.
    """

    CSV = "csv"
    XLSX = "xlsx"
    EXPORT_FORMAT_CHOICES = [
        (CSV, "CSV"),
        (XLSX, "Excel (.xlsx)"),
    ]

    default_export_format = models.CharField(
        max_length=10, choices=EXPORT_FORMAT_CHOICES, default=XLSX
    )
    home_address = models.CharField(
        max_length=500,
        blank=True,
        help_text="Visits whose name/address contain this text are hidden "
        "from the dashboard by default (e.g. your home address).",
    )

    class Meta:
        verbose_name = "Configuration"
        verbose_name_plural = "Configuration"

    def __str__(self) -> str:
        return "Nexus Logs configuration"

    @classmethod
    def get_solo(cls) -> "AppConfig":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
