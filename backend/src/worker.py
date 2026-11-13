import time
from pathlib import Path
from sqlalchemy import select
from redis import Redis
from src.config.database import Session
from src.config.settings import REDIS_URL
from src.models import RankingRun,SensitivityRun
from src.services.run_service import execute_run
from src.services.sensitivity_service import execute_sensitivity
redis=Redis.from_url(REDIS_URL)
while True:
    Path('/tmp/heartbeat').touch()
    with Session() as db:
        run=db.scalar(select(RankingRun).where(RankingRun.status.in_(['queued','running'])).order_by(RankingRun.id))
        sensitivity=db.scalar(select(SensitivityRun).where(SensitivityRun.status.in_(['queued','running'])).order_by(SensitivityRun.id))
        tasks=[('run',run),('sensitivity',sensitivity)]
        tasks=[t for t in tasks if t[1]]
        if tasks:
            kind,item=min(tasks,key=lambda t:(t[1].created_at,t[0]))
            if kind=='run':execute_run(db,item.id)
            else:execute_sensitivity(db,item.id)
        else:redis.brpop(['pairwise:runs','pairwise:sensitivity'],timeout=2)
    time.sleep(.1)
