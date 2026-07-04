from card import Bash, Defend, Strike
from character.encounters import nibbit
from fight import Fight
from character.player import Ironclad

# Attack, attack, attack! Prioritize cards in the following order: Bash, Strike, Defend. Spend all energy.
def unga_bunga_ironclad(fight: Fight) -> bool:
    player = fight.player

    bash = Bash()
    strike = Strike()
    defend = Defend()

    if player.hand[bash] > 0 and bash.playable(player.energy):
        player.play(bash, target=fight.enemies[0])

    elif player.hand[strike] > 0 and strike.playable(player.energy):
        player.play(strike, target=fight.enemies[0])

    elif player.hand[defend] > 0 and defend.playable(player.energy):
        player.play(defend, target=None)

    return player.energy == 0 or player.hand.total() == 0  # End turn if no energy left or hand is empty

if __name__ == "__main__":
    player = Ironclad(name="Ironchad", player_turn_callback=unga_bunga_ironclad)
    fight = Fight(player=player, enemies=nibbit(), verbose=True)

    fight.start()
