import pymongo


class DB():

    db_client = pymongo.MongoClient('127.0.0.1', serverSelectionTimeoutMS=2000)

    @staticmethod
    def check_connection():
        try: db_info = DB.db_client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError:
            print('Cannot connect to DB')
            return False

        print(f'Connected to MongoDB {db_info["version"]}')
        return True


    @staticmethod
    def get_db(collection):
        return DB.db_client['auto-loved-bot'][collection]


    @staticmethod
    def cleanup():
        DB.db_client.close()