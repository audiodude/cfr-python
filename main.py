import enum
import random

class Choice(enum.Enum):
  ROCK = 1
  PAPER = 2
  SCIS = 3

def utility(choice_a, choice_b):
  if choice_a == choice_b:
    return 0
  elif choice_a == Choice.ROCK:
    if choice_b == Choice.PAPER:
      return -1
    else:
      return 1
  elif choice_a == Choice.PAPER:
    if choice_b == Choice.SCIS:
      return -1
    else:
      return 1
  else:
    if choice_b == Choice.ROCK:
      return -1
    else:
      return 1

class RegretMatcher:
  def __init__(self):
    r, p, s = (random.random(), random.random(), random.random())
    normalizing_sum = r + p + s
    r /= normalizing_sum
    p /= normalizing_sum
    s /= normalizing_sum
    self.strategy = dict(zip(Choice, (r, p, s)))
    self.strategy_sum = dict((choice, 0) for choice in Choice)
    self.regret_sum = dict((choice, 0) for choice in Choice)

  def update_strategy(self):
    normalizing_sum = 0
    for choice, value in self.strategy.items():
      self.strategy[choice] = 0
      if self.regret_sum[choice] > 0:
        self.strategy[choice] = self.regret_sum[choice]
      normalizing_sum += self.strategy[choice]

    for choice, value in self.strategy.items():
      if normalizing_sum > 0:
        self.strategy[choice] /= normalizing_sum
      else:
        self.strategy[choice] = 1.0 / len(self.strategy)
      self.strategy_sum[choice] += self.strategy[choice]

  def action(self):
    rnd = random.random()
    a = 0
    cumulative_prob = 0
    for choice, prob in self.strategy.items():
      cumulative_prob += prob
      if rnd < cumulative_prob:
        return choice

  def update_regret_sum(self, my_action, opp_action):
    action_utility = dict((choice, utility(choice, opp_action))
                          for choice in Choice)

    self.regret_sum = dict(
      (choice, action_utility[choice] - action_utility[my_action])
      for choice in Choice)

  def get_average_strategy(self):
    normalizing_sum = 0
    avg_strategy = dict((choice, 0) for choice in Choice)
    normalizing_sum = sum(self.strategy_sum.values())
    for choice, sum_ in self.strategy_sum.items():
      if normalizing_sum > 0:
        avg_strategy[choice] = sum_ / normalizing_sum
      else:
        avg_strategy[choice] = -1

    return avg_strategy

def train():
  my_matcher = RegretMatcher()
  opp_matcher = RegretMatcher()

  for _ in range(10000):
    my_action = my_matcher.action()
    opp_action = opp_matcher.action()

    my_matcher.update_regret_sum(my_action, opp_action)
    my_matcher.update_strategy()

    opp_matcher.update_regret_sum(opp_action, my_action)
    opp_matcher.update_strategy()

  print(my_matcher.get_average_strategy())
  print(opp_matcher.get_average_strategy())

if __name__ == '__main__':
  train()
