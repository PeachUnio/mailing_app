# mailing/management/commands/send_mailings.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from mailing.models import Mailing, MailingLog
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta


class Command(BaseCommand):
    help = 'Отправляет рассылки, которые должны быть отправлены в данный момент'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mailing-id',
            type=int,
            help='ID конкретной рассылки для отправки (опционально)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительная отправка (игнорирует временные ограничения)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, какие рассылки будут отправлены, без реальной отправки',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        mailing_id = options.get('mailing_id')
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)

        self.stdout.write(self.style.SUCCESS(f'🔍 Поиск рассылок для отправки в {now.strftime("%d.%m.%Y %H:%M:%S")}'))

        if mailing_id:
            mailings = Mailing.objects.filter(id=mailing_id, is_active=True)
            if not mailings.exists():
                self.stdout.write(self.style.ERROR(f'❌ Рассылка с ID {mailing_id} не найдена или неактивна'))
                return
        else:
            mailings = Mailing.objects.filter(
                is_active=True,
                status__in=[Mailing.STATUS_RUNNING, Mailing.STATUS_CREATED],
                start_time__lte=now,
                end_time__gte=now,
            )

            recent_logs = MailingLog.objects.filter(
                mailing__in=mailings,
                attempt_time__gte=now - timedelta(hours=1)
            ).values_list('mailing_id', flat=True).distinct()

            mailings = mailings.exclude(id__in=recent_logs)

        count = mailings.count()
        self.stdout.write(f'📊 Найдено рассылок: {count}')

        if count == 0:
            self.stdout.write(self.style.WARNING('⏳ Нет рассылок для отправки'))
            return

        for mailing in mailings:
            self.stdout.write(
                f'  • #{mailing.id}: {mailing.message.letter_theme} ({mailing.recipients.count()} получателей)')

        if dry_run:
            self.stdout.write(self.style.SUCCESS('✅ Режим DRY-RUN: отправка не производилась'))
            return

        success_count = 0
        error_count = 0

        for mailing in mailings:
            self.stdout.write(f'\n📨 Отправка рассылки #{mailing.id}...')

            try:
                if force:
                    result = self._force_send_mailing(mailing)
                else:
                    result = mailing.send_mailing()

                if result[0]:
                    self.stdout.write(self.style.SUCCESS(f'  ✅ {result[1]}'))
                    success_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f'  ❌ {result[1]}'))
                    error_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Ошибка: {str(e)}'))
                error_count += 1

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS(f'✅ Отправка завершена:'))
        self.stdout.write(f'   Успешно: {success_count}')
        self.stdout.write(f'   С ошибками: {error_count}')
        self.stdout.write('=' * 50)

    def _force_send_mailing(self, mailing):
        """Принудительная отправка рассылки (игнорирует временные ограничения)"""
        success_count = 0
        error_count = 0

        for recipient in mailing.recipients.all():
            try:
                send_mail(
                    subject=mailing.message.letter_theme,
                    message=mailing.message.letter_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )

                MailingLog.objects.create(
                    mailing=mailing,
                    recipient=recipient,
                    status=MailingLog.STATUS_SUCCESS,
                    server_response="Email успешно отправлен (принудительно)",
                )
                success_count += 1

            except Exception as e:
                MailingLog.objects.create(
                    mailing=mailing,
                    recipient=recipient,
                    status=MailingLog.STATUS_FAILED,
                    server_response=str(e),
                )
                error_count += 1

        mailing.update_status()
        return True, f"Отправлено успешно: {success_count}, с ошибками: {error_count}"