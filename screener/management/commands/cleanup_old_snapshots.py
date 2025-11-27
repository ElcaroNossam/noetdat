"""
Management command to delete old ScreenerSnapshot records.

Deletes all snapshots older than 24 hours to keep the database size manageable.

Usage:
    python manage.py cleanup_old_snapshots
    python manage.py cleanup_old_snapshots --hours 48  # Custom retention period
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from screener.models import ScreenerSnapshot


class Command(BaseCommand):
    help = "Delete ScreenerSnapshot records older than specified hours (default: 24)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Delete snapshots older than this many hours (default: 24)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        dry_run = options["dry_run"]
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Get count of records to be deleted
        old_snapshots = ScreenerSnapshot.objects.filter(ts__lt=cutoff_time)
        count = old_snapshots.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"No snapshots older than {hours} hours found. Database is clean."
                )
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would delete {count} snapshots older than {hours} hours "
                    f"(before {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')})"
                )
            )
            
            # Show some examples
            examples = old_snapshots.order_by("ts")[:5]
            if examples:
                self.stdout.write("\nExample records that would be deleted:")
                for snapshot in examples:
                    self.stdout.write(
                        f"  - {snapshot.symbol.symbol} @ {snapshot.ts}"
                    )
            return
        
        # Actually delete
        self.stdout.write(
            f"Deleting {count} snapshots older than {hours} hours "
            f"(before {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')})..."
        )
        
        deleted_count = old_snapshots.delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully deleted {deleted_count} old snapshots."
            )
        )
        
        # Show remaining count
        remaining = ScreenerSnapshot.objects.count()
        self.stdout.write(f"Remaining snapshots in database: {remaining}")

