import enum
import random

class Actions(enum.Enum):
  CHECK = 'c'
  BET = 'b'
  FOLD = 'f'

  def __repr__(self):
    return self.value

class Node:
  def __init__(self, history, avail_actions):
    self.history = history
    self.avail_actions = avail_actions
    self.p0 = 0
    self.p1 = 0
    self.p2 = 0

    # Initialize strategy to randomness
    self.strategy = {}
    for a in self.avail_actions:
      self.strategy[a] = random.random()
    normalizing_sum = sum(self.strategy.values())
    for a in self.avail_actions:
      self.strategy[a] /= normalizing_sum

    self.strategy_sum = dict((a, 0) for a in self.avail_actions)
    self.regret_sum = dict((a, 0) for a in self.avail_actions)

  def __str__(self):
    return '<%s/%s: %r>' % (
      self.history, self.avail_actions, self.get_average_strategy())

  def update_strategy(self):
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
      self.strategy_sum[action] += self.p_player * self.strategy[action]

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
    avg_strategy = dict((a, 0) for a in self.avail_actions)
    normalizing_sum = sum(self.strategy_sum.values())
    for a, sum_ in self.strategy_sum.items():
      if normalizing_sum > 0:
        avg_strategy[a] = sum_ / normalizing_sum
      else:
        avg_strategy[a] = -1

    return avg_strategy

class KuhnThreeTrainer:
  def __init__(self):
    self.nodemap = {}

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

    # For each action, recursively call cfr with additional history and
    # probability
    probs = (p0, p1, p2)
    node.update_strategy(probs[player])
    util = {}
    node_util = 0
    for a in Actions:
      next_history = history + a.value
      if player == 0:
        util[a] = self.cfr(cards, next_history, p0 * node.strategy[a], p1, p2)
      elif player == 1:
        util[a] = self.cfr(cards, next_history, p0, p1 * node.strategy[a], p2)
      else:
        util[a] = self.cfr(cards, next_history, p0, p1, p2 * node.strategy[a])
      node_util += node.strategy[a] * util[a]

    for a in Actions:
      regret = util[a] - node_util
      node.regret_sum[a] += probs[player] * regret

    return node_util

  def get_available_actions(self, history):
    avail = list(Actions)
    if 'b' in history:
      avail.remove(Actions.CHECK)
    else:
      avail.remove(Actions.FOLD)
    return avail

  def is_terminal(self, history):
    if len(history) < 4:
      return
    last_three = history[-3:]
    return 'c' not in last_three or last_three == 'ccc'

  def generate_nodes(self, history):
    avail_actions = self.get_available_actions(history)
    self.nodemap[history] = Node(history, avail_actions)
    if self.is_terminal(history):
      return

    for a in avail_actions:
      self.generate_nodes(history + a.value)

  def train(self, iterations):
    cards = [1, 2, 3, 4]
    for c in cards:
      self.generate_nodes(str(c))

    util = 0
    for _ in range(iterations):
      random.shuffle(cards)

    for node in self.nodemap.values():
      print(node)

if __name__ == '__main__':
  kt = KuhnThreeTrainer().train(1)
