# auto-loved-bot

What it does: goes through multiplayer matches and counts how many times each person has played the maps. Each play is counted as a vote, and conditions for a vote to count are:
* The map played is graveyarded
* The player passed the map
* The player did not use any of the following mods: NF, EZ, HT, RX, AP
* The host did not put up a map made by them

A map is auto loved when 5 unique players have 3 votes each for a map

Requires mongoDB
