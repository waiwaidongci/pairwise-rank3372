from datetime import datetime
from sqlalchemy import String,ForeignKey,DateTime,JSON,Double
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class SensitivityRun(Base):
    __tablename__='sensitivity_runs'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(140),unique=True)
    run_id:Mapped[int]=mapped_column(ForeignKey('ranking_runs.id'))
    ridge:Mapped[float]=mapped_column(Double,default=1.)
    repeats:Mapped[int]=mapped_column(default=100)
    seed:Mapped[int]=mapped_column(default=20261112)
    status:Mapped[str]=mapped_column(String(20),default='queued')
    result:Mapped[dict]=mapped_column(JSON,default=dict)
    error:Mapped[str]=mapped_column(String(600),default='')
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
