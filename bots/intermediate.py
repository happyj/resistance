import random
import itertools

from player import Bot


def permutations(config):
    """Returns unique elements from a list of permutations."""
    return list(set(itertools.permutations(config)))


class Simpleton(Bot):
    """A bot that does logical reasoning based on the known spies and the
    results from the mission sabotages."""

    def onGameRevealed(self, players, spies):
        self.players = players
        self.spies = spies

        self.configurations = permutations([True, True, False, False])

    def getSpies(self, config):
        return [player for player, spy in zip(self.others(), config) if spy]

    def getResistance(self, config):
        return [player for player, spy in zip(self.others(), config) if not spy]

    def _validate(self, config, team, sabotaged):
        spies = [s for s in team if s in self.getSpies(config)]
        return len(spies) >= sabotaged

    def select(self, players, count):
        if self.configurations:
            # Pick one of the many options first, who knows...    
            config = self._select(self.configurations)
            # Now pick some random players with or without myself.
            return random.sample([self] + self.getResistance(config), count)
        else:
            assert self.spy
            return [self] + random.sample(self.others(), count - 1)

    def _select(self, configurations):
        """This is a hook for inserting more advanced reasoning on top of the
        maximal amount of logical reasoning you can perform."""
        return random.choice(configurations)
        
    def _acceptable(self, team):
        """Determine if this team is an acceptable one to vote for..."""
        current = [c for c in self.configurations if self._validate(c, team, 0)]
        return bool(len(current) > 0)

    def vote(self, team): 
        # If it's not acceptable, then we have to shoot it down.
        if not self._acceptable(team):
            return False
        # Otherwise we randomly pick a course of action, who knows?
        else:
            return self._vote(team)

    def _vote(self, team):
        """This is a hook for providing more complex voting once logical
        reasoning has been performed."""
        return random.choice([True, False])

    def onMissionComplete(self, sabotaged):
        self.configurations = [c for c in self.configurations if self._validate(c, self.game.team, sabotaged)]

    def sabotage(self):
        return self.game.turn > 1


class Bounder(Simpleton):
    """Idea of upper and lower bounds shamelessly stolen from Peter Cowling. :-)
       This is an implementation of his bot for comparison and modeling."""

    def onGameRevealed(self, players, spies):
        self.players = players
        self.spies = spies

        # The set of possible assignments around the table, for:
        #   - PESSIMISTIC: All teams except those 100% proven to be spies.
        self.pessimistic = permutations([True, True, False, False])
        #   - OPTIMISTIC: The teams we don't suspect to be spies without guarantees.
        self.optimistic = permutations([True, True, False, False])

    def select(self, players, count):
        if self.optimistic:
            config = random.choice(self.optimistic)
        else:
            assert len(self.pessimistic) > 0
            config = random.choice(self.pessimistic)
        return [self] + random.sample(self.getResistance(config), count-1)
    
    def vote(self, team): 
        # Determine if this is an acceptable thing to vote for...
        def acceptable(configurations, optimistic):
            current = [c for c in configurations if self._validate(c, team, 0, optimistic)]
            return bool(len(current) > 0)

        # Try our best-case options first, otherwise fall back...
        if self.optimistic:
            return acceptable(self.optimistic, True)
        elif self.pessimistic:
            return acceptable(self.pessimistic, False)
        else:
            return random.choice([True, False])

    def onVoteComplete(self, votes):
        # Speculation about votes does not guarantee anything, so we exclude
        # it here. See git history for details, or other bots like Invalidator.
        pass

    def _validate(self, config, team, sabotaged, optimistic):
        spies = [s for s in team if s in self.getSpies(config)]
        if optimistic:
            return len(spies) == sabotaged
        else:
            return len(spies) >= sabotaged

    def onMissionComplete(self, sabotaged):
        if self.spy:
            return

        self.optimistic = [c for c in self.optimistic if self._validate(c, self.game.team, sabotaged, True)]
        self.pessimistic = [c for c in self.pessimistic if self._validate(c, self.game.team, sabotaged, False)]

    def sabotage(self):
        return True 

