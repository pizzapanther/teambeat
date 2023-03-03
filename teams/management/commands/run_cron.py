import time

from django.core.management.base import BaseCommand, CommandError

import schedule

from teams.tasks import send_things


class Command(BaseCommand):
  help = 'run cron jobs'

  def handle(self, *args, **options):
    schedule.every(5).minutes.do(send_things)
    print('Loaded: team.tasks.send_things')

    while 1:
      schedule.run_pending()
      time.sleep(20)
