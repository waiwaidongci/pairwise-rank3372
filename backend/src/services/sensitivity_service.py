import json
from pathlib import Path
from sqlalchemy import select
from fastapi import HTTPException
from redis import Redis
from src.config.settings import REDIS_URL
from src.models import SensitivityRun
from src.services.run_service import get_run,active_task_count
from src.services.pair_omission import diagnose_omissions
from src.constants.enums import RunStatus
redis=Redis.from_url(REDIS_URL)
def list_sensitivity(db):return db.scalars(select(SensitivityRun).order_by(SensitivityRun.id.desc())).all()
def get_sensitivity(db,id):
    item=db.get(SensitivityRun,id)
    if not item:raise HTTPException(404,'逐对剔除诊断不存在')
    return item

def create_sensitivity(db,data):
    run=get_run(db,data.run_id)
    if run.status!=RunStatus.COMPLETED:raise HTTPException(409,'只可诊断已完成的拟合研究')
    if db.scalar(select(SensitivityRun).where(SensitivityRun.name==data.name)):raise HTTPException(409,'诊断名称已存在')
    if active_task_count(db)>=3:raise HTTPException(429,'已有3项活动任务，请等待完成')
    # Parameters are copied from the completed parent run: the diagnosis always
    # recomputes with the original ridge, repeats and seed.
    item=SensitivityRun(name=data.name,run_id=run.id,ridge=run.ridge,repeats=run.repeats,seed=run.seed,status=RunStatus.QUEUED);db.add(item);db.commit()
    # Database is authoritative; worker scans queued tasks even if Redis notification fails.
    try:redis.lpush('pairwise:sensitivity',str(item.id))
    except Exception:pass
    return item

def execute_sensitivity(db,id):
    item=get_sensitivity(db,id)
    if item.status not in ('queued','running'):return
    item.status=RunStatus.RUNNING;db.commit()
    try:
        run=get_run(db,item.run_id)
        parent={'run_id':run.id,'run_name':run.name,'fingerprint':run.result.get('fingerprint','')}
        # The frozen snapshot is the only input; live ledger rows are never read here.
        result=diagnose_omissions(run.snapshot,run.ridge,run.repeats,run.seed,parent,lambda:Path('/tmp/heartbeat').touch())
        Path('/artifacts').mkdir(exist_ok=True);Path(f'/artifacts/sensitivity-{id}.json').write_text(json.dumps(result,ensure_ascii=False,allow_nan=False))
        item.result=result;item.error='';item.status=RunStatus.COMPLETED;db.commit()
    except Exception as exc:
        db.rollback();item=get_sensitivity(db,id);item.status=RunStatus.FAILED;item.error=str(exc)[:600];db.commit()
