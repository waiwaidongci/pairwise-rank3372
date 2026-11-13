from src.services import sensitivity_service as service
def index(db):return service.list_sensitivity(db)
def create(db,data):return service.create_sensitivity(db,data)

def detail(db,id):return service.get_sensitivity(db,id)
