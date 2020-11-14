import enum
import random

class Actions(enum.Enum):
  PASS = 'p'
  BET = 'b'

  def __repr__(self):
    return self.value

class Node:
  def __init__(self, infoset):
    self.infoset = infoset

    # Initialize strategy to randomness
    self.strategy = {}
    for a in Actions:
      self.strategy[a] = random.random()
    normalizing_sum = sum(self.strategy.values())
    for a in Actions:
      self.strategy[a] /= normalizing_sum

    self.strategy_sum = dict((a, 0) for a in Actions)
    self.regret_sum = dict((a, 0) for a in Actions)

  def __str__(self):
    return '<%4s: %r>' % (self.infoset, self.get_average_strategy())

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

class KuhnTrainer:
  def __init__(self):
    self.nodemap = {}

  def cfr(self, cards, history, p0, p1):
    plays = len(history)
    player = plays % 2
    opponent = 1 - player

    # Check for terminal states and return payoff
    if plays > 1:
      terminal_pass = history[plays - 1] == 'p'
      double_bet = history[plays - 2:plays] == 'bb'
      is_player_card_higher = cards[player] > cards[opponent];

      if terminal_pass:
        if history == 'pp':
          return 1 if is_player_card_higher else -1
        else:
          return 1
      elif double_bet:
        return 2 if is_player_card_higher else -2

    infoset = str(cards[player]) + history
    # Get information set node or create if non-existant
    node = self.nodemap.get(infoset, Node(infoset))
    self.nodemap[infoset] = node

    # For each action, recursively call cfr with additional history and
    # probability
    node.update_strategy(p0 if player == 0 else p1)
    util = dict((a, 0) for a in Actions)
    node_util = 0
    for a in Actions:
      next_history = history + a.value
      if player == 0:
        util[a] -= self.cfr(cards, next_history, p0 * node.strategy[a], p1)
      else:
        util[a] -= self.cfr(cards, next_history, p0, p1 * node.strategy[a])
      node_util += node.strategy[a] * util[a]

    for a in Actions:
      regret = util[a] - node_util
      node.regret_sum[a] += (p0 if player == 0 else p1) * regret

    return node_util

  def train(self, iterations):
    cards = [1, 2, 3]
    util = 0
    for _ in range(iterations):
      random.shuffle(cards)
      util += self.cfr(cards, '', 1, 1)

    print('Average game value: %s' % (util / iterations))
    for node in self.nodemap.values():
      print(node)

if __name__ == '__main__':
  kt = KuhnTrainer().train(100000)
