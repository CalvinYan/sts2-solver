from collections import Counter

from card import Card, Strike, Defend, Bash, AscendersBane
from character.player import Player

class Ironclad(Player):
    draw_pile: Counter[Card] = Counter({
        Strike(): 5,
        Defend(): 5,
        Bash(): 1,
        AscendersBane(): 1,
    })
