import datetime
from db import DB


class LovedDB():

    collection = 'loved'

    @staticmethod
    def add_loved_map(map_id):
        collection = DB.get_db(LovedDB.collection)

        cursor = collection.find_one({ '_id' : map_id})
        if not cursor: collection.insert_one({ '_id' : map_id, 'date' : datetime.datetime.utcnow() })
        else: del cursor


    @staticmethod
    def load_loved_maps():
        """
        format:
            [ map_id (int), ... ]
        """
        collection = DB.get_db(LovedDB.collection)
        cursor = collection.find()

        # Process
        data = cursor.distinct('_id')
        if cursor: del cursor
        return data


    @staticmethod
    def is_loved_map(map_id):
        collection = DB.get_db(LovedDB.collection)

        # Update
        query = { '_id' : map_id }
        cursor = collection.find_one(query)

        # Process
        if not cursor: result = False
        else:          result = True

        if cursor: del cursor
        return result