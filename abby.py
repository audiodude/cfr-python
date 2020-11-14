import enum
import random

class Actions(enum.Enum):
  CHECK = 'k'
  BET = 'b'
  CALL = 'c'
  FOLD = 'f'
  RAISE = 'r'

  def __repr__(self):
    return self.value

class Round:
  def __init__(self, actions=None, player_acting=0):
    if actions is not None:
      self.actions = actions
    else:
      self.actions = []
    self.player_acting = player_acting

  def __str__(self):
    return ''.join(repr(a) for a in self.actions) + str(self.player_acting)

  def next_(self, action):
    return Round(
      self.actions[:] + [action], 1 if self.player_acting == 0 else 0)

  def available_actions(self):
    available = list(Actions)
    if Actions.BET in self.actions:
      available.remove(Actions.CHECK)
      available.remove(Actions.BET)
    else:
      available.remove(Actions.FOLD)
      available.remove(Actions.CALL)
      available.remove(Actions.RAISE)
    if Actions.RAISE in self.actions and Actions.RAISE in available:
      available.remove(Actions.RAISE)
    return available

  def is_terminal(self):
    if len(self.actions) == 0:
      return False
    if self.actions[-1] == Actions.FOLD or self.actions[-1] == Actions.CALL:
      return True
    if (len(self.actions) > 1 and
        self.actions[0] == Actions.CHECK and
        self.actions[1] == Actions.CHECK):
      return True

class Node:
  def __init__(self, infoset):
    self.infoset = infoset

    self.reset_strategy()
    self.strategy_sum = dict((a, 0) for a in Actions)
    self.regret_sum = dict((a, 0) for a in Actions)

  def __str__(self):
    return '<%s: %r>' % (self.infoset, self.get_average_strategy())

  def __repr__(self):
    return 'N'

  def reset_strategy(self):
    # Initialize strategy to randomness
    self.strategy = {}
    for a in Actions:
      self.strategy[a] = random.random()
    normalizing_sum = sum(self.strategy.values())
    for a in Actions:
      self.strategy[a] /= normalizing_sum

  def update_strategy(self, realization_weight):
    normalizing_sum = 0
    for action, value in self.strategy.items():
      self.strategy[action] = 0
      if self.regret_sum[action] > 0:
        self.strategy[action] = self.regret_sum[action]
      normalizing_sum += self.strategy[action]

    for action, value in self.strategy.items():
      if normalizing_sum > 0:
        self.strategy[action] /= normalizing_sum
      else:
        self.strategy[action] = 1.0 / len(self.strategy)
      self.strategy_sum[action] += realization_weight * self.strategy[action]

  def action(self):
    rnd = random.random()
    a = 0
    cumulative_prob = 0
    for action, prob in self.strategy.items():
      cumulative_prob += prob
      if rnd < cumulative_prob:
        return action

  def get_average_strategy(self):
    normalizing_sum = 0
    avg_strategy = dict((a, 0) for a in Actions)
    normalizing_sum = sum(self.strategy_sum.values())
    for a, sum_ in self.strategy_sum.items():
      if normalizing_sum > 0:
        avg_strategy[a] = sum_ / normalizing_sum
      else:
        avg_strategy[a] = -1

    for a in Actions:
      if avg_strategy[a] < 0.001:
        avg_strategy[a] = 0
    normalizing_sum = sum(avg_strategy.values())
    if normalizing_sum > 0:
      for a in Actions:
        avg_strategy[a] /= normalizing_sum

    return avg_strategy

class AbbyTrainer:
  move_value = {
    Actions.BET: 1,
    Actions.RAISE: 2,
    Actions.CALL: 1,
  }

  def __init__(self):
    self.nodemap = {}

  def calculate_pot(self, history):
    pot = 2
    for round_ in history:
      for move in round_.actions:
        pot += self.move_value.get(move, 0)
    return pot

  def calculate_player_bet(self, history, player):
    amt = 1
    for round_ in history:
      for i, move in enumerate(round_.actions):
        if i % 2 == player:
          amt += self.move_value.get(move, 0)
    return amt

  def cfr(self, cards, history, p0, p1):
    round_ = history[-1]
    is_last_round = len(history) == 2
    player = round_.player_acting

    # Check for terminal states and return payoff
    if round_.is_terminal():
      pot = self.calculate_pot(history)
      if round_.actions[-1] == Actions.FOLD:
        return pot
      
      if is_last_round:
        player_cards = cards[player*3:player*3+3]
        opp_cards = cards[(1-player)*3:(1-player)*3+3]
        if sum(player_cards) > sum(opp_cards):
          return pot
        else:
          return -1 * self.calculate_player_bet(history, player)

    if len(history) == 1:
      infoset = ''.join(str(c) for c in cards[player*3:player*3+2])
      infoset += '+%s' % cards[(1-player)*3]
      infoset += ' %s' % ''.join(str(r) for r in history)
    else:
      infoset = ''.join(str(c) for c in cards[player*3:player*3+3])
      infoset += '+%s' % cards[(1-player)*3]
      infoset += ' %s' % ''.join(str(r) for r in history)
    infoset = infoset.replace('10', 'T')

    # Get information set node or create if non-existant.
    node = self.nodemap.get(infoset, Node(infoset))
    self.nodemap[infoset] = node

    # For each action, recursively call cfr with additional history and
    # probability.
    probs = (p0, p1)
    node.update_strategy(probs[player])
    util = dict((a, 0) for a in Actions)
    node_util = 0

    # Start a new round.
    if round_.is_terminal():
      round_ = Round()
      history = (history[0], round_)

    for a in round_.available_actions():
      if len(history) == 2:
        next_history = (history[0], round_.next_(a))
      else:
        next_history = (round_.next_(a),)

      if player == 0:
        util[a] -= self.cfr(cards, next_history, p0 * node.strategy[a], p1)
      elif player == 1:
        util[a] -= self.cfr(cards, next_history, p0, p1 * node.strategy[a])
      node_util += node.strategy[a] * util[a]

    for a in round_.available_actions():
      regret = util[a] - node_util
      node.regret_sum[a] += probs[player] * regret

    return node_util

  def train(self, iterations):
    cards = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    util = 0
    has_reset = False
    for i in range(iterations):
      if i % 100 == 0:
        print(i)
      random.shuffle(cards)
      util += self.cfr(tuple(cards), (Round(),), 1, 1)

      # if not has_reset and i > iterations / 2:
      #   for node in self.nodemap.values():
      #     node.reset_strategy()
      #   has_reset = True

    print('Average game value: %s' % (util / iterations))
    for node in self.nodemap.values():
      print(node)

if __name__ == '__main__':
  at = AbbyTrainer().train(100000)
