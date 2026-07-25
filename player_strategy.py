"""Simulates Floor 2 fights with user input, allowing you to compare how you stack up against algorithms"""

from collections import defaultdict

from card import Bash, Card, Defend, Strike, Targeting
from character.encounters import ALL_ENCOUNTERS
from character.player import Ironclad
from compare_strategies import has_lethal
from fight import Fight
from search.table import QTable

CARDS: dict[str, Card] = {"s": Strike(), "d": Defend(), "b": Bash()}
dp_table: QTable = QTable.load("./data/solver/all.csv.pkl.gz")


# Play your way! Displays your hand, draw pile, and discard pile, and reads the next decision from user input.
class Customclad(Ironclad):
    def resolve_turn(self, fight: Fight) -> bool:
        print(fight)

        print("Lines:")
        for card in CARDS.values():
            state_action: tuple[tuple[int, ...], tuple[int, ...]]
            if card.targeting == Targeting.ENEMY_SINGLE:
                for i in range(len(fight.enemies)):
                    state_action = (fight.to_vector(), (card.id, i))
                    if state_action in dp_table:
                        print(f"{card.__class__.__name__} on enemy {i}: {dp_table[state_action]}")
            else:
                state_action = (fight.to_vector(), (card.id,))
                if state_action in dp_table:
                    print(f"{card.__class__.__name__}: {dp_table[state_action]}")
        state_action = (fight.to_vector(), (-1,))
        if state_action in dp_table:
            print(f"End turn: {dp_table[state_action]}")

        if has_lethal(fight):
            print("YOU HAVE LETHAL!")
            return True

        cmds = input("""
To play a card in your hand, enter its first letter
For multi-enemy fights, to target an enemy, type its position number (0-4)
To end your turn, type "e"
For example: "b 0 d e"
""").split()

        print()

        i = 0
        while i < len(cmds):
            cmd = cmds[i]
            if cmd == "e":
                if i != len(cmds) - 1:
                    print(f"The following cards would not be played after ending your turn: {cmds[i+1:]}")
                    return False
            elif cmd not in CARDS:
                print(f"Invalid command at position {i}: {cmd}")
                return False  # Prompt again
            else:
                card = CARDS[cmd]
                if card.targeting == Targeting.ENEMY_SINGLE:
                    if len(fight.enemies) > 1:
                        i += 1
                        if not (i < len(cmds) and cmds[i].isdigit() and int(cmds[i]) in range(len(fight.enemies))):
                            print(f"Invalid target for card {card.__class__.__name__}")
                            return False
            i += 1

        i = 0
        while i < len(cmds):
            cmd = cmds[i]
            if cmd == "e":
                return True

            card = CARDS[cmd]
            if self.hand.cards[card] > 0 and self.can_play(card):
                if card.targeting == Targeting.ENEMY_SINGLE:
                    if len(fight.enemies) > 1:
                        i += 1
                        if i < len(cmds) and cmds[i].isdigit() and int(cmds[i]) in range(len(fight.enemies)):
                            self.play(card, target=fight.enemies[int(cmds[i])])
                        else:
                            print(f"Invalid target for card {card.__class__.__name__}")
                            return False
                    else:
                        self.play(card, target=fight.enemies[0])
                else:
                    self.play(card)
            else:
                print(f"Could not play card {card} at position {i}")
                return False  # Prompt again
            i += 1

        return self.energy == 0


if __name__ == "__main__":
    hp_losses = defaultdict(list)

    for encounter in ALL_ENCOUNTERS:
        for _ in range(20):
            player = Customclad(name="User")
            starting_hp = player.hp
            fight = Fight(player=player, enemies=encounter(verbose=True))
            fight.start()

            print(f"You lost {starting_hp - player.hp} hp")
            hp_losses[encounter].append(starting_hp - player.hp)

    for encounter in ALL_ENCOUNTERS:
        print(f"HP losses against {encounter.__name__}: {hp_losses[encounter]}")
        print(
            f"Average HP loss of against {encounter.__name__}: {sum(hp_losses[encounter]) / len(hp_losses[encounter])}"
        )
