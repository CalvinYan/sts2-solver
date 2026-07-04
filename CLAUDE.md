# 1. ANY DEVIATION FROM INSTRUCTION IS A CRITICAL FAILURE
If at any point during operation you notice that your task, methodology, or scope contradict what was prompted, you must immediately terminate and provide the following information:
* What you were asked to do
* How you deviated from what was asked
* What changes you made prior to termination 

# 2. Write code, not mechanics
Successful simulation of Slay the Spire 2 is dependent on understanding its mechanics and rules. Although you may have knowledge of these, you may not make code changes solely based on that knowledge. You MAY identify potential errors in implementing game mechanics, or ask the user to confirm game mechanics if your work requires it. 
  
For example, the following code is incorrect because Vulnerable increases damage taken, not damage dealt. While this may seem intuitive, it still constitutes game knowledge. You should not attempt to correct this logic by yourself, but should call it out if your work comes across it during a user session.
```py
class Vulnerable(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.damage is not None:
            move.action.damage = int(move.action.damage * 1.5)
```

In contrast, the following code is obviously incorrect, and requires no game knowledge to understand why:
```py
def take_damage(self, damage: int) -> None:
    self.hp = max(0, damage - self.block) # Should say -= instead of =
    self.block = max(0, self.block - damage)
```

# For Github Actions
The following instructions apply ONLY to Claude Code Github Actions.  

You are being asked to make minor improvements to the code in this repository. Your scope is the entire repository.
  
Minor improvements are limited to the following:
* Fixing obvious mistakes in game logic (see rule 2 above)
* Fixing errors that would prevent code from running in the root directory (i.e. compilation errors, circular imports, null pointer exceptions)
* Optimizing code (removing duplicated code, improving list comprehensions to be more readable, etc)

They do not include:
* Implementing new features
* Writing unit tests
* Modifying the code's file structure / class structure (unless it is strictly necessary for the above)

For each improvement, raise a pull request according to the following format:
### What
What code changes were made in this pull request?

### Why
Why are they beneficial?

### Notes
Anything a human would need to know to continue maintaining the code, such as
* Necessary follow-up changes
* Modifications to user interfaces
* New failure modes introduced

This should be blank in most cases.
