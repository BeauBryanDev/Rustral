from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.config import Config
import logging


class Database:
    
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        """
        Implement the Singleton pattern to ensure only one instance of 
        the Database class is created.
        """
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._connect()
        return cls._instance

    def _connect(self):
        """
        Set up the connection to MongoDB using the URI from the configuration.
        """
        try:
            # Start up the client 
            self._client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
            
            # Force a connection to check if MongoDB is reachable
            self._client.admin.command('ping')
            
            # Extract the database name from the URI and connect to it
            db_name = Config.MONGO_URI.split('/')[-1].split('?')[0] or "fractorust_db"
            self._db = self._client[db_name]
            
            logging.info(f"🔌 Conexión a MongoDB establecida: {Config.MONGO_URI}")
            
        except ConnectionFailure as e:
            
            logging.error(f"Error crítico: No se pudo conectar a MongoDB. {e}")
            raise e


    @property
    def db(self):
        """
        Returns the database object.
        """
        return self._db

    def close_connection(self):
        """
        Close the connection to MongoDB.
        """
        if self._client:
            self._client.close()
            logging.info("🔌 Conexión a MongoDB cerrada.")



# Create a single instance of the Database class
db_instance = Database()

