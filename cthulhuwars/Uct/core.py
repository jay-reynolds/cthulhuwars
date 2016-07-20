from __future__ import division

import time
from math import log, sqrt
from random import choice


class MonteCarlo(object):
    def __init__(self, board, **kwargs):
        self.board = board
        self.states = []
        self.wins = {}
        self.plays = {}

        self.max_depth = 0
        self.stats = {}

        self.calculation_time = float(kwargs.get('time', 30))
        self.max_moves = int(kwargs.get('max_moves', 1000))

        # Exploration constant, increase for more exploratory moves,
        # decrease to prefer moves with known higher win rates.
        self.C = float(kwargs.get('C', 1.4))

    def update(self, state):
        self.states.append(state)

    def display(self, state, play):
        return self.board.display(state, play)

    def winner_message(self, msg):
        return self.board.winner_message(msg)

    def get_play(self):
        # Causes the AI to calculate the best move from the
        # current game state and return it.

        self.max_depth = 0
        self.stats = {}

        state = self.states[-1]
        player = self.board.current_player(state)
        legal = self.board.legal_plays(self.states[:])

        # Bail out early if there is no real choice to be made.
        if not legal:
            return
        if len(legal) == 1:
            return legal[0]

        games = 0
        begin = time.time()
        while time.time() - begin < self.calculation_time:
            self.run_simulation()
            games += 1

        # Display the number of calls of `run_simulation` and the
        # time elapsed.
        self.stats.update(games=games, max_depth=self.max_depth,
                          time=str(time.time() - begin))
        print self.stats['games'], self.stats['time']
        print "Maximum depth searched:", self.max_depth

        moves_states = [(p, self.board.next_state(state, p)) for p in legal]

        # Display the stats for each possible play.
        self.stats['moves'] = sorted(
            ({'move': p,
              'percent': 100 * self.wins.get((player, S), 0) / self.plays.get((player, S), 1),
              'wins': self.wins.get((player, S), 0),
              'plays': self.plays.get((player, S), 0)}
             for p, S in moves_states),
            key=lambda x: (x['percent'], x['plays']),
            reverse=True
        )
        for m in self.stats['moves']:
            print "{move}: {percent:.2f}% ({wins} / {plays})".format(**m)

        # Pick the move with the highest percentage of wins.
        percent_wins, num_moves, move = max(
            (self.wins.get((player, S), 0) /
             self.plays.get((player, S), 1),
             self.plays.get((player, S), 0),
             p)
            for p, S in moves_states
        )

        return move

    def run_simulation(self):
        # Plays out a "random" game from the current position,
        # then updates the statistics tables with the result.

        # A bit of an optimization here, so we have a local
        # variable lookup instead of an attribute access each loop.
        plays, wins = self.plays, self.wins

        visited_states = set()
        states_copy = self.states[:]
        state = states_copy[-1]
        player = self.board.current_player(state)

        expand = True
        for t in xrange(1, self.max_moves + 1):
            legal = self.board.legal_plays(states_copy)
            moves_states = [(p, self.board.next_state(state, p)) for p in legal]

            if all(plays.get((player, S)) for p, S in moves_states):
                # If we have stats on all of the legal moves here, use UCB1.
                log_total = log(
                    sum(plays[(player, S)] for p, S in moves_states))
                value, move, state = max(
                    ((wins[(player, S)] / plays[(player, S)]) +
                     self.C * sqrt(log_total / plays[(player, S)]), p, S)
                    for p, S in moves_states
                )
            else:
                # Otherwise, just make an arbitrary decision.
                move, state = choice(moves_states)

            states_copy.append(state)

            # `player` here and below refers to the player
            # who moved into that particular state.
            if expand and (player, state) not in plays:
                expand = False
                plays[(player, state)] = 0
                wins[(player, state)] = 0
                if t > self.max_depth:
                    self.max_depth = t

            visited_states.add((player, state))

            player = self.board.current_player(state)
            winner = self.board.winner(states_copy)
            if winner:
                break

        for player, state in visited_states:
            if (player, state) not in plays:
                continue
            plays[(player, state)] += 1
            if player == winner:
                wins[(player, state)] += 1


class ValueMonteCarlo(object):
    def __init__(self, board, **kwargs):
        self.board = board
        self.states = []

        self.values = {}
        self.plays = {}

        self.max_depth = 0
        self.stats = {}

        self.calculation_time = float(kwargs.get('time', 30))
        self.max_moves = int(kwargs.get('max_moves', 1000))

        # Exploration constant, increase for more exploratory moves,
        # decrease to prefer moves with known higher win rates.
        self.C = float(kwargs.get('C', 1.4))

    def update(self, state):
        self.states.append(state)

    def display(self, state, play):
        return self.board.display(state, play)

    def winner_message(self, msg):
        return self.board.winner_message(msg)

    def get_play(self):
        # Causes the AI to calculate the best move from the
        # current game state and return it.

        self.values.clear()
        self.plays.clear()

        self.max_depth = 0
        self.stats = {}

        state = self.states[-1]
        player = self.board.current_player(state)
        legal = self.board.legal_plays(self.states[:])

        # Bail out early if there is no real choice to be made.
        if not legal:
            return
        if len(legal) == 1:
            return legal[0]

        games = 0
        begin = time.time()
        while time.time() - begin < self.calculation_time:
            self.run_simulation()
            games += 1

        # Display the number of calls of `run_simulation` and the
        # time elapsed.
        self.stats.update(games=games, max_depth=self.max_depth,
                          time=str(time.time() - begin))
        print self.stats['games'], self.stats['time']
        print "Maximum depth searched:", self.max_depth

        moves_states = [(p, self.board.next_state(state, p)) for p in legal]

        # Display the stats for each possible play.
        self.stats['moves'] = sorted(
            ({'move': p,
              'average': self.values.get((player, S), 0) / self.plays.get((player, S), 1),
              'sum': self.values.get((player, S), 0),
              'plays': self.plays.get((player, S), 0)}
             for p, S in moves_states),
            key=lambda x: (x['average'], x['plays']),
            reverse=True
        )
        for m in self.stats['moves']:
            print "{move}: {average:.1f} ({sum} / {plays})".format(**m)

        # Pick the move with the highest average value.
        average, num_moves, move = max(
            (self.values.get((player, S), 0) /
             self.plays.get((player, S), 1),
             self.plays.get((player, S), 0),
             p)
            for p, S in moves_states
        )

        return move

    def run_simulation(self):
        # Plays out a "random" game from the current position,
        # then updates the statistics tables with the result.

        # A bit of an optimization here, so we have a local
        # variable lookup instead of an attribute access each loop.
        plays, values = self.plays, self.values

        visited_states = set()
        states_copy = self.states[:]
        state = states_copy[-1]
        player = self.board.current_player(state)

        expand = True
        for t in xrange(1, self.max_moves + 1):
            legal = self.board.legal_plays(states_copy)
            moves_states = [(p, self.board.next_state(state, p)) for p in legal]

            if all(plays.get((player, S)) for p, S in moves_states):
                # If we have stats on all of the legal moves here, use UCB1.
                log_total = log(
                    sum(plays[(player, S)] for p, S in moves_states))
                value, move, state = max(
                    ((values[(player, S)] / plays[(player, S)]) +
                     self.C * sqrt(log_total / plays[(player, S)]), p, S)
                    for p, S in moves_states
                )
            else:
                # Otherwise, just make an arbitrary decision.
                move, state = choice(moves_states)

            states_copy.append(state)

            # `player` here and below refers to the player
            # who moved into that particular state.
            if expand and (player, state) not in plays:
                expand = False
                plays[(player, state)] = 0
                values[(player, state)] = 0
                if t > self.max_depth:
                    self.max_depth = t

            visited_states.add((player, state))

            player = self.board.current_player(state)
            winner = self.board.winner(states_copy)
            if winner:
                break

        player_values = {}
        for player, state in visited_states:
            if (player, state) not in plays:
                continue
            if player not in player_values:
                player_values[player] = self.board.end_value(states_copy, player)

            plays[(player, state)] += 1
            if player_values[player] is not None:
                values[(player, state)] += player_values[player]

