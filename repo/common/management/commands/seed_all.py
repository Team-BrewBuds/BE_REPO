import os

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "모든 더미 데이터를 한 번에 생성 (settings 따라 dev 또는 prod 모드)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            default=10,
            type=int,
            help="더미 데이터를 생성할 개수",
        )

    def handle(self, *args, **kwargs):
        number = kwargs["number"]
        settings = kwargs["settings"]
        mode = settings.split(".")[-1]

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)

        commands = [
            "seed_user_and_details",
            "seed_beans",
            "seed_tasted_records",
            "seed_posts",
            "seed_photos",
            "seed_comments",
            "seed_notes",
        ]

        try:
            with transaction.atomic():
                for command in commands:
                    self.stdout.write(self.style.SUCCESS(f"Running {command}..."))
                    call_command(command, number=number)
                self.stdout.write(self.style.SUCCESS(f"[{mode}] 모든 시드 데이터 생성 완료!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            self.stdout.write(self.style.ERROR(f"[{mode}] 시드 데이터 생성 실패!"))
