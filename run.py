import threading
import requests
import time

from online import Online
from match_db import MatchDb
from auto_loved import AutoLoved
from db import DB


class AutoLovedBot():

    # Hardcoded match id to start with when there is a blank slate
    LATEST_MATCH_ID = 61862100

    # Rate in seconds how often to check for new matches
    MATCH_CHECK_RATE = 4

    # Rate in seconds how often to check for new events in matches
    EVENT_CHECK_RATE = 5

    # Max allowable amount of concurrent match monitors
    MAX_MATCH_MONITORS = 5

    @staticmethod
    def run():
        AutoLovedBot.monitors = {}
        AutoLovedBot.monitors_lock = threading.Lock()
        AutoLovedBot.match_id = AutoLovedBot.load_saved_match_monitors()

        if not DB.check_connection():
            return

        print('Starting core loop...')

        while True:
            time.sleep(AutoLovedBot.MATCH_CHECK_RATE)

            # Wait until resources have freed up before checking next match id
            if len(AutoLovedBot.monitors) >= AutoLovedBot.MAX_MATCH_MONITORS:
                continue

            print(f'Checking match: {AutoLovedBot.match_id}')
            try: status, _ = Online.fetch_web_data(f'https://osu.ppy.sh/community/matches/{AutoLovedBot.match_id}/history?after=0&limit=1')
            except requests.exceptions.ReadTimeout:
                print('Read timeout')
                continue

            # Wait a second and get data again
            if status == Online.REQUEST_RETRY:
                continue

            # Unavailable, go to next one
            if status == Online.REQUEST_BAD:
                AutoLovedBot.match_id += 1
                continue

            # Create a match monitor and go to next one
            if status == Online.REQUEST_OK:
                # Start a match monitor
                monitor = threading.Thread(target=AutoLovedBot.new_match_monitor, args=(AutoLovedBot.match_id, 0))
                monitor.setDaemon(True)
                monitor.start()

                # Store the match monitor in memory
                with AutoLovedBot.monitors_lock:
                    AutoLovedBot.monitors[AutoLovedBot.match_id] = monitor

                print(f'New match monitor: {AutoLovedBot.match_id}, Total match monitors: {len(AutoLovedBot.monitors)}')
                AutoLovedBot.match_id += 1


    @staticmethod
    def cleanup():
        DB.cleanup()


    @staticmethod
    def load_saved_match_monitors():
        latest_match_id = AutoLovedBot.LATEST_MATCH_ID
        data = MatchDb.load_saved_match_monitor_data()

        # If there are no saved match monitors, get latest stopping point
        if data == None:
            match_id, event_id = MatchDb.load_latest_match_data()

            # If there is no latest stopping point, used hard coded value
            if match_id == None or event_id == None:
                return latest_match_id

            # Just put it in the format the following code expects it in 
            data = [ { '_id' : match_id, 'event_id' : event_id } ]

        print('Loading saved match monitor states...')

        # Go through saved match monitoring progress and create match monitors based on that data
        for match_data in data:
            match_id = match_data['_id']
            event_id = match_data['event_id']
            print(f'Loading saved state: {match_id}, {event_id}')

            # Start a match monitor
            monitor = threading.Thread(target=AutoLovedBot.new_match_monitor, args=(match_id, event_id))
            monitor.setDaemon(True)
            monitor.start()

            # Store the match monitor in memory
            with AutoLovedBot.monitors_lock:
                AutoLovedBot.monitors[match_id] = monitor

            # While at it, figure out what the latest match id that has been looked at
            latest_match_id = max(latest_match_id, match_id)

        # Return latest match ID to kickstart mainloop
        return latest_match_id


    @staticmethod
    def new_match_monitor(match_id, event_id):
        # Match monitor loop
        while True:
            try:
                time.sleep(AutoLovedBot.EVENT_CHECK_RATE) 
                status, data = Online.fetch_web_data(f'https://osu.ppy.sh/community/matches/{match_id}/history?after={event_id}&limit=50')
            except requests.exceptions.ReadTimeout:
                print('Read timeout')
                continue

            # TODO: Is this possible?
            #if status == Online.REQUEST_BAD:
            #    TODO: Idk what to do with this yet

            # Maybe the internet went out or osu! servers are on fire. Wait a bit and try again
            if status == Online.REQUEST_RETRY:
                continue

            # If there are no new events, wait a bit and see if there are
            if len(data['events']) == 0:
                continue

            for event in data['events']:
                # Check if match is disbanded. If so, stop monitoring it
                event_type = event['detail']['type']
                if event_type == 'match-disbanded':
                    MatchDb.destroy_match_monitor_data(match_id)
                    with AutoLovedBot.monitors_lock:
                        if match_id in AutoLovedBot.monitors:
                            del AutoLovedBot.monitors[match_id]

                    print(f'Removed match monitor: {match_id}')
                    return

                # At this point the match will be continued to be monitored. Save progress.
                event_id = event['id']
                MatchDb.save_match_monitor_data(match_id, event_id)    

                # Event type 'other' contains match results: map info, and play info
                if event_type == 'other':
                    try: map_status = event['game']['beatmap']['beatmapset']['status']
                    except:
                        # I think this happens when there is an unsubmited map
                        print(f'!!! Failed getting match data - {match_id} : {event_id}')
                        continue

                    timestamp = event['timestamp']
                    print(f'New match event - {match_id} : {event_id}, map status: {map_status},  time: {timestamp}')

                    # Count only graveyarded maps because we don't want to auto love
                    # something that is being worked on, or potentially for rank
                    if map_status != 'graveyard': continue

                    # Filter out unapproved mods
                    match_mods = event['game']['mods']
                    if AutoLovedBot.is_unapproved_mods(match_mods): continue

                    # Map and play data
                    gamemode   = event['game']['mode']
                    title      = event['game']['beatmap']['beatmapset']['title']
                    version    = event['game']['beatmap']['version']
                    creator    = event['game']['beatmap']['beatmapset']['creator']
                    creator_id = event['game']['beatmap']['beatmapset']['user_id']
                    map_id     = event['game']['beatmap']['id']
                    player_ids = []

                    # Go through the scores and filter out ones we doesn't care about
                    scores = event['game']['scores']
                    for score in scores:
                        # A special case where creator puts up their own beatmap
                        # This shouldn't count. Invalidate everything, and go to next event.
                        if score['user_id'] == creator_id:
                            player_ids = []
                            break

                        # TODO: Check what maps other players have submitted and make sure non of the players
                        # have their map put up. Meant to prevent mapper passing host to others players to bypass
                        # this filter.

                        if AutoLovedBot.is_unapproved_mods(score['mods']): continue
                        if score['multiplayer']['pass'] == 0: continue
                        player_ids.append(score['user_id'])

                    # Nothing to add votes for if so
                    if len(player_ids) == 0:
                        continue

                    # We got data, now give it to AutoLoved for processing
                    AutoLoved.add_votes_for_map(gamemode, title, version, creator, map_id, player_ids)
                

    @staticmethod
    def is_unapproved_mods(mods):
        if 'NF' in mods: return True  # No NF because that's not a valid pass
        if 'EZ' in mods: return True  # No EZ because the map is prob too hard for the player, making it invalid vote (although thats questionable in std)
        if 'HT' in mods: return True  # No HT because the map is prob too hard for the player, making it invalid vote
        #if 'SO' in mods: return True  # Maybe, not sure
        if 'RX' in mods: return True  # Lol, no
        if 'AP' in mods: return True  # Also no

        return False


if __name__ == '__main__':
    try:
        AutoLovedBot.run()
    except KeyboardInterrupt:
        print('Shutting down...')
    finally: 
        AutoLovedBot.cleanup()

    exit(0)
    