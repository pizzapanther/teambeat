from django.core.management.base import BaseCommand, CommandError

from teams.tasks import send_scrums, send_reports


class Command(BaseCommand):
  help = 'kick off scrum send task'

  def add_arguments(self, parser):
    parser.add_argument('team_ids', nargs='*', type=int)
    parser.add_argument('--sync', action='store_true')

  def handle(self, *args, **options):
    if options['sync']:
      send_scrums(options['team_ids'])
      send_reports(options['team_ids'])

    else:
      send_scrums.send(options['team_ids'])
      send_reports.send(options['team_ids'])
