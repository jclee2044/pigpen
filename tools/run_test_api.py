"""Disposable synthetic API for browser tests. Never reads production configuration."""
from pathlib import Path
import sys
import tempfile
import argparse
from datetime import datetime,timezone
from uuid import uuid4
from pydantic import TypeAdapter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from pigpen.config import Settings
from pigpen.database import migrate
from pigpen.app import create_app
import uvicorn
parser=argparse.ArgumentParser()
parser.add_argument('--port',type=int,default=8765)
parser.add_argument('--demo',action='store_true')
parser.add_argument('--static',action='store_true')
args=parser.parse_args()
with tempfile.TemporaryDirectory(prefix='pigpen-browser-test-') as directory:
    settings=Settings(Path(directory),'test',static_dir=ROOT/'frontend/dist' if args.static else None)
    migrate(settings)
    if args.demo:
        from pigpen.service import Service
        from pigpen.database import Database
        from pigpen.contracts import Operation
        from zoneinfo import ZoneInfo
        service=Service(Database(settings))
        def command(kind,data,actor=None):
            op=TypeAdapter(Operation).validate_python(dict(operation_id=str(uuid4()),entity_id=str(uuid4()),actor_id=actor,client_time=datetime.now(timezone.utc),kind=kind,data=data))
            return service.execute(op)['result']
        command('household.initialize',{'name':'Demo household'})
        alex=command('user.create',{'name':'Alex'})
        command('user.create',{'name':'Jamie','avatar':{'background':'sage','hat':'beret','bandana':'teal'}})
        from sqlalchemy import select
        from pigpen.schema import categories
        with Database(settings).transaction() as connection:
            cats={x['name']:x['id'] for x in connection.execute(select(categories)).mappings()}
        day=datetime.now(ZoneInfo('America/New_York')).date().isoformat()
        command('budget.set',{'month':day[:7],'expected_income_minor':400000,'allocations':[{'category_id':cats[name],'amount_minor':amount} for name,amount in [('Housing',160000),('Food',50000),('Gas',15000),('Dates',20000),('Savings',30000),('Alex Personal',20000)]]},alex['id'])
        for item,amount,category in [('Weekly groceries',8640,'Food'),('Books for the weekend',3000,'Alex Personal'),('Fuel for the week',4200,'Gas')]:
            command('purchase.create',{'item':item,'amount_minor':amount,'category_id':cats[category],'transaction_date':day},alex['id'])
        command('request.create',{'item':'A picnic together','amount_minor':6500,'description':'A small weekend plan.'},alex['id'])
    uvicorn.run(create_app(settings),host='127.0.0.1',port=args.port,log_level='warning')
