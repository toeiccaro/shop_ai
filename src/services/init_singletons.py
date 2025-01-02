from src.services.deepface_service import DeepFaceSingleton
from src.services.postgres_service import PostgresConnectionSingleton

# Initialize the singletons and return as a tuple
def init_singletons():
    deepface_instance = DeepFaceSingleton.get_instance()
    db_instance = PostgresConnectionSingleton.get_instance()
    return deepface_instance, db_instance
