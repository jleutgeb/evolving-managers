import random
import numpy as np
import matplotlib as mlp
import matplotlib.pyplot as plt
import operator
import statistics


# elements are weighted by weights
def weighted_choice(elems, weights):
    total = sum(weights)
    rand = random.uniform(0, total)
    cur_sum = 0
    for i, w in enumerate(weights):
        cur_sum += w
        if rand < cur_sum:
            return elems[i]
    return elems[-1]


def show_stats(simulation, stat):  # options for stat: 'q_history', 'p_manager_history', 'p_firm_history', 'a_history'
    x = [s + 1 for s in range(simulation.t)]
    market_history = []
    for i in range(simulation.m):
        decision_average = [0 for s in range(simulation.t)]
        for j in range(simulation.n):
            if stat == 'q_history':
                player_stat = simulation.markets[i][j].q_history
            elif stat == 'p_manager_history':
                player_stat = simulation.markets[i][j].p_manager_history
            elif stat == 'p_firm_history':
                player_stat = simulation.markets[i][j].p_firm_history
            else:
                player_stat = simulation.markets[i][j].a_history
            decision_average = list(map(operator.add, decision_average, player_stat))
        decision_average = [s * (1/simulation.n) for s in decision_average]
        market_history = market_history + [decision_average]

    market_average = []
    lowest_market = []
    highest_market = []
    variance_history = []
    for t in range(simulation.t):
        lowest = market_history[0][t]
        average = 0
        highest = market_history[0][t]
        variance_list = []
        for i in range(len(market_history)):
            average = average + market_history[i][t]
            if lowest > market_history[i][t]:
                lowest = market_history[i][t]
            if highest < market_history[i][t]:
                highest = market_history[i][t]
            variance_list = variance_list + [market_history[i][t]]
        average = average/len(market_history)
        market_average = market_average + [average]
        lowest_market = lowest_market + [lowest]
        highest_market = highest_market + [highest]
        variance_history = variance_history + [statistics.variance(variance_list)]

    fig, (ax1, ax2) = plt.subplots(ncols=2, nrows=1, constrained_layout=False, num=None, figsize=(12, 6))
    if stat == 'q_history':
        fig.suptitle('Decisions (q)')
        ax1.set_title("Decision history")
        ax1.set_ylabel('Decision (q)')
        ax1.axis([1, simulation.t, 0, 1])
    elif stat == 'p_manager_history':
        fig.suptitle('Manager Profit')
        ax1.set_title("Manager Profit history")
        ax1.set_ylabel('Manager Profit')
        ax1.set(xlim=(1, simulation.t))
    elif stat == 'p_firm_history':
        fig.suptitle('Firm Profit')
        ax1.set_title("Firm Profit history")
        ax1.set_ylabel('Firm Profit')
        ax1.set(xlim=(1, simulation.t))
    else:
        fig.suptitle('Overconfidence (a)')
        ax1.set_title("Overconfidence history")
        ax1.set_ylabel('Overconfidence (a)')
        ax1.axis([1, simulation.t, 0, 2])

    ax1.set_xlabel('round')
    ax1.plot(x, market_average, 'b-', label='average')
    ax1.plot(x, lowest_market, 'r-', label='lowest')
    ax1.plot(x, highest_market, 'g-', label='highest')
    ax1.legend()

    ax2.set_title("variance history")
    ax2.set_ylabel('variance')
    ax2.set_xlabel('round')
    ax2.set(xlim=(1, simulation.t))
    ax2.plot(x, variance_history, 'b-', label='variance')
    ax2.legend()

    plt.show()


def payoff_function_manager(gamma, c, a, q, other_qs):
    payoff_sum = 0
    for other_q in other_qs:
        pay = c * q * (a - q - gamma * other_q)
        payoff_sum += max(pay, 0)
    payoff = payoff_sum/len(other_qs)
    return payoff


def payoff_function_firm(gamma, c, q, other_qs):
    payoff_sum = 0
    for other_q in other_qs:
        pay = c * q * (1 - q - gamma * other_q)
        payoff_sum += max(pay, 0)
    payoff = payoff_sum/len(other_qs)
    return payoff


def best_choice_slow(gamma, c, player, other_players, previous_round):
    best_p = player.p_manager_history[previous_round]
    best_q = player.q_history[previous_round]
    a = player.a_history[previous_round]
    other_qs = []
    for other_player in other_players:
        other_qs = other_qs + [other_player.q_history[previous_round]]
    for i in range(0, 101):
        if payoff_function_manager(gamma, c, a, i/100, other_qs) > best_p:
            best_p = payoff_function_manager(gamma, c, a, i/100, other_qs)
            best_q = i/100
    return best_q


def half_way_best_choice_slow(gamma, c, player, other_players, previous_round):
    best_p = player.p_manager_history[previous_round]
    old_q = player.q_history[previous_round]
    best_q = player.q_history[previous_round]
    a = player.a_history[previous_round]
    other_qs = []
    for other_player in other_players:
        other_qs = other_qs + [other_player.q_history[previous_round]]
    for i in range(0, 101):
        if payoff_function_manager(gamma, c, a, i/100, other_qs) > best_p:
            best_p = payoff_function_manager(gamma, c, a, i/100, other_qs)
            best_q = i/100
    return old_q + (best_q - old_q)/2


def best_choice_wrong(gamma, c, player, other_players, previous_round):
    a = player.a_history[previous_round]
    other_qs = []
    for other_player in other_players:
        other_qs = other_qs + [other_player.q_history[previous_round]]
    best_q = (1/2)*(a-gamma*sum(other_qs)/len(other_players))
    return best_q


def half_way_best_choice_wrong(gamma, c, player, other_players, previous_round):
    old_q = player.q_history[previous_round]
    a = player.a_history[previous_round]
    other_qs = []
    for other_player in other_players:
        other_qs = other_qs + [other_player.q_history[previous_round]]
    best_q = (1 / 2) * (a - gamma * sum(other_qs) / len(other_players))
    return old_q + (best_q - old_q)/2


def mimic_choice(gamma, c, player, other_players, previous_round):
    best_p = player.p_manager_history[previous_round]
    best_q = player.q_history[previous_round]
    for i in range(len(other_players)):
        if other_players[i].p_manager_history[previous_round] > best_p:
            best_q = other_players[i].q_history[previous_round]
    return best_q


def always_half(gamma, c, player, other_players, previous_round):
    return 0.5


def uniform_noise(lower, upper, mean, variance):
    return random.uniform(lower, upper)


def normal_noise(lower, upper, mean, variance):
    return random.normalvariate(mean, variance)


class Simulation:
    n = 4                               # number of players
    a_min = 0.5                         # confidence parameter min/mas
    a_max = 1.5
    q_min = 0                           # quantity choice/decision min/max
    q_max = 1
    t = 150                             # number of rounds/ticks
    m = 50                              # number of markets
    gamma = 0.5                         # substitutability
    c = 1                               # scalar
    initial_a = 1
    initial_q = 0.5
    evolution_every_x_rounds = 5
    noise_uniform_lower = -0.1
    noise_uniform_upper = 0.1
    noise_normal_mean = 0
    noise_normal_variance = 0.1
    noise_func = uniform_noise
    prob_evolv_min = 0
    prob_evolv_max = 0.8
    prob_imitation_min = 0
    prob_imitation_max = 0.8
    choice_func = always_half
    evo_mech = 'best'
    markets = []

    def __init__(self, parameters):
        # assigning parameters
        try:
            self.n = parameters['n']
        except KeyError:
            print('parameter n missing, default taken')
        try:
            self.a_min = parameters['a_min']
        except KeyError:
            print('parameter a_min missing, default taken')
        try:
            self.a_max = parameters['a_max']
        except KeyError:
            print('parameter a_max missing, default taken')
        try:
            self.q_min = parameters['q_min']
        except KeyError:
            print('parameter q_min missing, default taken')
        try:
            self.q_max = parameters['q_max']
        except KeyError:
            print('parameter q_max missing, default taken')
        try:
            self.t = parameters['t']
        except KeyError:
            print('parameter t missing, default taken')
        try:
            self.m = parameters['m']
        except KeyError:
            print('parameter m missing, default taken')
        try:
            self.gamma = parameters['gamma']
        except KeyError:
            print('parameter gamma missing, default taken')
        try:
            self.c = parameters['c']
        except KeyError:
            print('parameter c missing, default taken')
        try:
            self.initial_a = parameters['initial_a']
        except KeyError:
            print('parameter initial_a missing, default taken')
        try:
            self.initial_q = parameters['initial_q']
        except KeyError:
            print('parameter initial_q missing, default taken')
        try:
            self.evolution_every_x_rounds = parameters['evolution_every_x_rounds']
        except KeyError:
            print('parameter evolution_every_x_rounds missing, default taken')
        try:
            self.noise_uniform_lower = parameters['noise_uniform_lower']
        except KeyError:
            print('parameter noise_uniform_lower missing, default taken')
        try:
            self.noise_uniform_upper = parameters['noise_uniform_upper']
        except KeyError:
            print('parameter noise_uniform_upper missing, default taken')
        try:
            self.noise_normal_mean = parameters['noise_normal_mean']
        except KeyError:
            print('parameter noise_normal_mean missing, default taken')
        try:
            self.noise_normal_variance = parameters['noise_normal_variance']
        except KeyError:
            print('parameter noise_normal_variance missing, default taken')
        try:
            self.prob_evolv_min = parameters['prob_evolv_min']
        except KeyError:
            print('parameter prob_evolv_min missing, default taken')
        try:
            self.prob_evolv_max = parameters['prob_evolv_max']
        except KeyError:
            print('parameter prob_evolv_max missing, default taken')
        try:
            self.prob_imitation_min = parameters['prob_imitation_min']
        except KeyError:
            print('parameter prob_imitation_min missing, default taken')
        try:
            self.prob_imitation_max = parameters['prob_imitation_max']
        except KeyError:
            print('parameter prob_imitation_max missing, default taken')
        try:
            self.choice_func = parameters['choice_func']
        except KeyError:
            print('parameter choice_func missing, default taken')
        try:
            self.noise_func = parameters['noise_func']
        except KeyError:
            print('parameter noise_func missing, default taken')
        try:
            self.evo_mech = parameters['evo_mech']
        except KeyError:
            print('parameter evo_mech missing, default taken')

        # initiate players in markets
        for i in range(self.m):
            group = []
            for j in range(self.n):
                group.append(Player(self.a_min, self.a_max, self.q_min, self.q_max))
            self.markets.append(group)

    def run_simulation(self):
        g = self.gamma
        c = self.c
        lower = self.noise_uniform_lower
        upper = self.noise_uniform_upper
        mean = self.noise_normal_mean
        variance = self.noise_normal_variance
        for i in range(self.t-1):

            # chose q phase
            for market in self.markets:
                for player in market:
                    other_players = market + []
                    other_players.remove(player)
                    new_q = self.choice_func(g, c, player, other_players, i)
                    new_q += self.noise_func(lower, upper, mean, variance)
                    if new_q > 1:
                        new_q = 1
                    elif new_q < 0:
                        new_q = 0
                    player.q_history = player.q_history+[new_q]

            # calc p phase
            for market in self.markets:
                for player in market:
                    q = player.q_history[-1]
                    other_players = market + []
                    other_players.remove(player)
                    other_qs = []
                    for other_player in other_players:
                        other_qs = other_qs + [other_player.q_history[-1]]
                    a = player.a_history[-1]
                    player.p_manager_history = player.p_manager_history+[payoff_function_manager(g, c, a, q, other_qs)]
                    player.p_firm_history = player.p_firm_history + [payoff_function_firm(g, c, q, other_qs)]

            # Evolution selection
            if i % self.evolution_every_x_rounds == 0:
                # prob evolution
                for market in self.markets:
                    prob_list = list(np.linspace(self.prob_evolv_min, self.prob_evolv_max, self.n))
                    fitness_list = []
                    players = market + []
                    for player in players:
                        fitness_list = fitness_list + [player.p_firm_history[-1]]
                    prob_list = [x for _, x in sorted(zip(fitness_list, prob_list), key=lambda pair: pair[0])]
                    prob_list.reverse()
                    for j in range(len(players)):
                        random_num = random.random()
                        if prob_list[j] > random_num:
                            players[j].evolv = True
                        else:
                            players[j].evolv = False

                # imitation weighted_average (as in models.py)
                if self.evo_mech == 'weighted_average':
                    for market in self.markets:
                        all_payoff_windows = []
                        prev_a_vars = []
                        for player in market:
                            all_payoff_windows = all_payoff_windows + [player.p_firm_history[-1]]
                            prev_a_vars = prev_a_vars + [player.a_history[-1]]
                        for player in market:
                            if player.evolv:
                                avg_payoff_window = sum(all_payoff_windows) / len(all_payoff_windows)
                                weights = [max(0, poff - avg_payoff_window) for poff in all_payoff_windows]

                                new_a = weighted_choice(prev_a_vars, weights)
                                new_a += self.noise_func(lower, upper, mean, variance)
                            else:
                                new_a = player.a_history[-1]
                            player.a_history = player.a_history + [new_a]

                # imitation best
                if self.evo_mech == 'best':
                    for market in self.markets:
                        players = market + []
                        best_player = sorted(players, key=lambda play: play.p_firm_history[-1], reverse=False)[-1]
                        for player in market:
                            if player.evolv:
                                new_a = best_player.a_history[-1] + self.noise_func(lower, upper, mean, variance)
                                player.a_history = player.a_history + [new_a]
                            else:
                                player.a_history = player.a_history + [player.a_history[-1]]

            # round without evolv
            else:
                for market in self.markets:
                    for player in market:
                        player.a_history = player.a_history + [player.a_history[-1]]


class Player:
    a_history = []
    q_history = []
    p_manager_history = []      # payoff
    p_firm_history = []         # fitness value
    evolv = False

    def __init__(self, a_min, a_max, q_min, q_max):
        self.a_history = [uniform_noise(a_min, a_max, 0, 0)]
        self.q_history = [uniform_noise(q_min, q_max, 0, 0)]
        self.p_manager_history = [0]
        self.p_firm_history = [0]


if __name__ == "__main__":
    para = dict(
        n=2,                          # number of players
        a_min=0.5,                    # confidence parameter initial min/mas
        a_max=1.5,
        q_min=0,                      # quantity choice/decision initial min/max
        q_max=1,
        t=300,                        # number of rounds/ticks
        m=50,                         # number of markets
        gamma=1,                      # substitutability
        c=1,                          # scalar
        initial_a=1,                  # obsolete (ignore)
        initial_q=0.5,                # obsolete (ignore)
        evolution_every_x_rounds=2,
        noise_uniform_lower=-0.05,
        noise_uniform_upper=0.05,
        noise_normal_mean=0,
        noise_normal_variance=0.1,
        noise_func=uniform_noise,     # uniform_noise or normal_noise
        prob_evolv_min=0.2,
        prob_evolv_max=0.8,
        prob_imitation_min=0,       # unused?
        prob_imitation_max=0.8,     # unused?
        choice_func=best_choice_slow,
        evo_mech='weighted_average'             # 'best' or 'weighted_average' (as in models.py)
    )

    sim = Simulation(para)
    sim.run_simulation()
    print(sim.markets[0][1].p_manager_history)
    print(len(sim.markets[0][1].p_manager_history))
    print(sim.markets[0][1].q_history)
    print(len(sim.markets[0][1].q_history))

    show_stats(sim, 'q_history')
    show_stats(sim, 'p_manager_history')
    show_stats(sim, 'p_firm_history')
    show_stats(sim, 'a_history')

    """
    plt.title('decision of player 1')
    plt.xlabel('round')
    plt.ylabel('decision (q)')
    x = [i+1 for i in range(150)]
    y = sim.markets[0][1].q_history
    plt.plot(x, y, 'r-')
    plt.axis([1, 150, 0, 1])
    plt.show()

    plt.title('payoff of player 1')
    plt.xlabel('round')
    plt.ylabel('payoff (p)')
    x = [i + 1 for i in range(150)]
    y = sim.markets[0][1].p_manager_history
    plt.plot(x, y, 'r-')
    plt.axis([1, 150, 0, 1])
    plt.show()

    plt.title('payoff of firm 1')
    plt.xlabel('round')
    plt.ylabel('payoff (p)')
    x = [i + 1 for i in range(150)]
    y = sim.markets[0][1].p_firm_history
    plt.plot(x, y, 'r-')
    plt.axis([1, 150, 0, 1])
    plt.show()

    plt.title('a of player 1')
    plt.xlabel('round')
    plt.ylabel('a')
    x = [i + 1 for i in range(150)]
    y = sim.markets[0][1].a_history
    plt.plot(x, y, 'r-')
    plt.axis([1, 150, 0, 2])
    plt.show()
    """
