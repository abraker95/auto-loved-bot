
from votes_db import VotesDB
from loved_db import LovedDB


class AutoLoved():

    # How many votes from unique players are required
    # \TODO: This needs to be a self adjusting value in response to desired rate of map promotion
    votes_unique_players = 5

    # How many votes from each unique player is required
    votes_per_player = 3

    @staticmethod
    def add_votes_for_map(gamemode, title, version, creator, map_id, player_ids):
        print(f'Map vote - Map id: {map_id}, {gamemode} | {title} [{version}] by {creator}')

        # Load votes for map, apply new counts, and save the new counts
        vote_data = VotesDB.load_map_votes(map_id)
        for player_id in player_ids:
            if not str(player_id) in vote_data:
                vote_data[str(player_id)] = 1
                print(f'\tPlayer vote - {player_id} : {vote_data[str(player_id)]}')
            else:
                # TODO: Store date of vote so that spam playing can be mitigated
                vote_data[str(player_id)] += 1
                print(f'\tPlayer vote - {player_id} : {vote_data[str(player_id)]}')

        VotesDB.save_map_votes(map_id, vote_data)

        # Now that we have new vote count, check if
        # that qualifies the map for auto loved.
        if AutoLoved.map_can_be_loved(vote_data):
            AutoLoved.make_map_autoloved(map_id)


    @staticmethod
    def map_can_be_loved(vote_data):
        # Check if number of unique players is less than required
        if len(vote_data) < AutoLoved.votes_unique_players:
            return False

        # Tally up all the unique players that have played the map enough times
        number_good_votes = 0
        for votes in vote_data.values():
            if votes >= AutoLoved.votes_per_player:
                number_good_votes += 1

        # Check if the tally matches unique players required
        return number_good_votes >= AutoLoved.votes_unique_players


    @staticmethod
    def make_map_autoloved(map_id):
        print(f'Map loved: {map_id}')
        LovedDB.add_loved_map(map_id)

        # TODO: notify endpoints