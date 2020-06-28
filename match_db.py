from db import DB


class MatchDb():

    collection = 'matches'
    collection_settings = 'settings'

    @staticmethod
    def save_match_monitor_data(match_id, event_id):
        collection = DB.get_db(MatchDb.collection)

        # Request
        query = { '_id' : match_id }
        value = { 'event_id' : event_id }
        collection.update_one(query, { '$set' : value }, upsert=True)

        # To check whether to update with latest stopping point to know where bot left off
        latest_match_id, latest_event_id = MatchDb.load_latest_match_data()

        # This means there is no stopping point saved... save it
        if latest_match_id == None or latest_event_id == None:
            MatchDb.save_latest_match_data(match_id, event_id)
            return
        
        # This means the match/event being looked at right now is later than saved
        if match_id > latest_match_id or event_id > latest_event_id:
            MatchDb.save_latest_match_data(match_id, event_id)
            return
            


    @staticmethod
    def load_saved_match_monitor_data():
        """
        format:
        [
            { '_id' : match_id (int), 'event_id' : latest_event_id (int) },
            { '_id' : match_id (int), 'event_id' : latest_event_id (int) },
            ...
        ]
        """
        collection = DB.get_db(MatchDb.collection)
        cursor = collection.find({})

        # Process
        data = list(cursor) 
        if len(data) == 0: 
            data = None

        del cursor
        return data


    @staticmethod
    def destroy_match_monitor_data(match_id):
        collection = DB.get_db(MatchDb.collection)

        query = { '_id' : match_id }
        collection.delete_one(query)


    @staticmethod
    def save_latest_match_data(match_id, event_id):
        collection = DB.get_db(MatchDb.collection_settings)

        # Request
        query = { '_id' : 'latest' }
        value = { 'match_id' : match_id, 'event_id' : event_id }
        collection.update_one(query, { '$set' : value }, upsert=True)

    
    @staticmethod
    def load_latest_match_data():
        collection = DB.get_db(MatchDb.collection_settings)
        cursor = collection.find_one({ '_id' : 'latest' })

        # Process
        if not cursor: latest_match_id, latest_event_id = None, None
        else: latest_match_id, latest_event_id = cursor['match_id'], cursor['event_id']

        if cursor: del cursor
        return latest_match_id, latest_event_id