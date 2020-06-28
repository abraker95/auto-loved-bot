from db import DB


class VotesDB():

    collection = 'votes'

    @staticmethod
    def save_map_votes(map_id, vote_data):
        collection = DB.get_db(VotesDB.collection)

        # Update
        query = { '_id'   : map_id }
        value = { 'plays' : vote_data }
        collection.update_one(query, { "$set" : value }, upsert=True)


    @staticmethod
    def load_map_votes(map_id):
        """
        format:
        {
            {user_id} : plays (int),
            {user_id} : plays (int),
            ...
        }
        """
        collection = DB.get_db(VotesDB.collection)

        # Request
        query  = { '_id' : map_id }
        cursor = collection.find_one(query)

        # Process
        if not cursor: data = {}
        else: data = cursor['plays']

        if cursor: del cursor
        return data