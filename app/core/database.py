import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.config import Config
import logging


class Database:
    
    _instance = None
    _client = None
    _db = None
    _connected = False

    def __new__(cls):
        """
        Implement the Singleton pattern to ensure only one instance of 
        the Database class is created.
        """
        if cls._instance is None:
            
            cls._instance = super(Database, cls).__new__(cls)
            
            # Only connect immediately if not in test environment
            if os.getenv('PYTEST_CURRENT_TEST') is None:
                
                cls._instance._connect()
                
        return cls._instance


    def _connect(self):
        """
        Set up the connection to MongoDB using the URI from the configuration.
        """
        if self._connected:
            return
            
        try:
            # Start up the client 
            self._client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
            
            # Force a connection to check if MongoDB is reachable
            self._client.admin.command('ping')
            
            # Extract the database name from the URI and connect to it
            db_name = Config.MONGODB_URI.split('/')[-1].split('?')[0] or "fractorust_db"
            self._db = self._client[db_name]
            self._connected = True
            
            logging.info(f"Connectiong to MongoDB: {Config.MONGODB_URI}")
            
        except ConnectionFailure as e:
            
            logging.error(f"Error, Unable to connect to MongoDB: {e}")
            raise e

    def ensure_connected(self):
        """
        Ensure the database connection is established.
        """
        if not self._connected:
            self._connect()

    @property
    def db(self):
        """
        Returns the database object.
        """
        self.ensure_connected()
        return self._db

    def close_connection(self):
        """
        Close the connection to MongoDB.
        """
        if self._client:
            self._client.close()
            self._connected = False
            logging.info(" Conexión a MongoDB cerrada.")



# Create a single instance of the Database class
db_instance = Database()

