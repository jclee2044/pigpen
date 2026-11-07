"""Explicit operator commands; no filesystem changes on import."""
import argparse
from pathlib import Path
from .config import Settings
from .database import Database, migrate
from .recovery import backup, restore, scheduled_backup
from .push import deliver_once, generate_vapid_key


def main():
    parser=argparse.ArgumentParser(prog='python -m pigpen')
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('migrate',help='Upgrade only the explicitly configured database')
    commands.add_parser('check',help='Check the configured database schema readiness')
    serve=commands.add_parser('serve');serve.add_argument('--host',default='127.0.0.1');serve.add_argument('--port',type=int,default=8000)
    save=commands.add_parser('backup');save.add_argument('destination',type=Path)
    schedule=commands.add_parser('backup-scheduled',help='Keep seven daily and four weekly full backups in a dedicated root')
    schedule.add_argument('destination',type=Path)
    load=commands.add_parser('restore');load.add_argument('source',type=Path);load.add_argument('destination',type=Path)
    load.add_argument('--environment',choices=['development','production'],required=True)
    commands.add_parser('deliver-once',help='Attempt one due outbox job; schedule repeated calls externally')
    keygen=commands.add_parser('vapid-keygen',help='Create a new private P-256 key outside the checkout')
    keygen.add_argument('destination',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='vapid-keygen':
            generate_vapid_key(args.destination)
            print('Private key created outside the checkout')
            return
        if args.command=='restore':
            restore(args.source,args.destination,args.environment)
            print('Restored into a new directory; configure it explicitly before use')
            return
        settings=Settings.from_env()
        if args.command=='migrate':
            migrate(settings);print('Schema upgraded')
        elif args.command=='check':
            ready=Database(settings).ready();print('Ready' if ready else 'Not ready')
            raise SystemExit(0 if ready else 1)
        elif args.command=='backup':
            backup(settings,args.destination);print('Backup verified')
        elif args.command=='backup-scheduled':
            scheduled_backup(settings,args.destination);print('Daily and weekly backups verified; retention applied')
        elif args.command=='deliver-once':
            print('Job processed' if deliver_once(Database(settings)) else 'No due jobs')
        elif args.command=='serve':
            from .app import create_app
            import uvicorn
            if not Database(settings).ready():
                raise ValueError('Run migrate explicitly before serving')
            uvicorn.run(create_app(settings),host=args.host,port=args.port,workers=1)
    except (ValueError,FileExistsError) as exc:
        parser.error(str(exc))


if __name__=='__main__':
    main()
