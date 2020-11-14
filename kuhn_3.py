import enum
import random

class Actions(enum.Enum):
  CHECK = 'c'
  BET = 'b'
  FOLD = 'f'

  def __repr__(self):
    return self.value

class Node:
  def __init__(self, infoset):
    self.infoset = infoset

    self.reset_strategy()
    self.strategy_sum = dict((a, 0) for a in Actions)
    self.regret_sum = dict((a, 0) for a in Actions)

  def __str__(self):
    return '<%4s: %r>' % (self.infoset, self.get_average_strategy())

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
    for a in Actions:
      avg_strategy[a] /= normalizing_sum

    return avg_strategy

class KuhnTrainer:
  def __init__(self):
    self.nodemap = {}

  # @memoize
  def cfr(self, cards, history, p0, p1, p2):
    player = len(history) % 3

    # Check for terminal states and return payoff
    if len(history) > 1:
      last_three = history[-3:]

      # Play is only terminal if a player hasn't checked in last three moves.
      # Or, if all players have checked in the last three moves.
      if 'c' not in last_three or last_three == 'ccc':
        # Check who's folded
        opponents = [0, 1, 2]
        for i, h in enumerate(history):
          if h == 'f':
            opponents.remove(i % 3)

        is_player_card_highest = True
        for opp in opponents:
          if cards[opp] > cards[player]:
            is_player_card_highest = False
            break

        if last_three == 'ccc':
          return 3 if is_player_card_highest else -1
        elif last_three.count('f') == 2:
          # Everyone else folded
          return history.count('b') + 3
        else:
          return history.count('b') + 3 if is_player_card_highest else -2

    infoset = str(cards[player]) + history
    # Get information set node or create if non-existant
    node = self.nodemap.get(infoset, Node(infoset))
    self.nodemap[infoset] = node

    # For each action, recursively call cfr with additional history and
    # probability
    probs = (p0, p1, p2)
    node.update_strategy(probs[player])
    util = {}
    node_util = 0
    
    available_actions = list(Actions)
    if 'b' in history:
      available_actions.remove(Actions.CHECK)
    else:
      available_actions.remove(Actions.FOLD)

    for a in available_actions:
      next_history = history + a.value
      if player == 0:
        util[a] = self.cfr(cards, next_history, p0 * node.strategy[a], p1, p2)
      elif player == 1:
        util[a] = self.cfr(cards, next_history, p0, p1 * node.strategy[a], p2)
      elif player == 2:
        util[a] = self.cfr(cards, next_history, p0, p1, p2 * node.strategy[a])
      node_util += node.strategy[a] * util[a]

    for a in available_actions:
      regret = util[a] - node_util
      node.regret_sum[a] += probs[player] * regret

    return node_util

  def train(self, iterations):
    cards = [1, 2, 3, 4]
    util = 0
    has_reset = False
    for i in range(iterations):
      random.shuffle(cards)
      util += self.cfr(tuple(cards), '', 1, 1, 1)

      if not has_reset and i > iterations / 2:
        for node in self.nodemap.values():
          node.reset_strategy()
        has_reset = True

    print('Average game value: %s' % (util / iterations))
    print(len(self.nodemap))
    for node in self.nodemap.values():
      print(node)

if __name__ == '__main__':
  kt = KuhnTrainer().train(50000)
