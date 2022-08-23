from argparse import Action
from os import stat
from otree.api import *
import time
import random


doc = """
Your app description
"""

class C(BaseConstants):
    NAME_IN_URL = 'evolving_managers'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 60 # number of supergames
    POPULATION_SIZE = 6 # population size/matching silo size
    ACTION_DECIMAL_PLACES = 3 # how fine is the action grid (bounded by 0 and 1). with 3 it's 0, 0.001, 0.002, etc


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    gamma = models.FloatField()  # substitutability between firms' goods
    p1_action = models.FloatField() # player 1's choice in the current period (q)
    p2_action = models.FloatField() # player 2's choice in the current period (q)
    p1_period_payoff = models.FloatField() # player 1's payoff (not profit) in the current period
    p2_period_payoff = models.FloatField() # player 2's payoff (not profit) in the current period
    expected_timestamp = models.FloatField() # when is the period expected to happen
    period = models.IntegerField(initial=0) # current period the group is in
    supergame_started = models.BooleanField(initial=False) # track whether the supergame has started


class Player(BasePlayer):
    population = models.IntegerField() # track population/matching silo
    confidence = models.FloatField() # player's confidence (a)
    action = models.FloatField() # current choice (q)
    period_payoff = models.FloatField() # payoff in last period
    round_payoff = models.FloatField(initial=0) # cumulative payoff in current supergame
    period_fitness = models.FloatField() # fitness (firm profit) in last period
    period = models.IntegerField(initial=0) # tracks current period for player
    timestamp = models.FloatField() # timestamp in milliseconds
    round_fitness = models.FloatField(initial=0) # cumulative fitness (firm profit) in current round
    ready = models.BooleanField(initial=False) # track whether the player is ready for the supergame to start 
    rank = models.IntegerField() # firm's fitness rank at the end of the supergame
    prob_selection = models.FloatField() # probability that a firm selects the current manager out (i.e. draws a new confidence)
    weight = models.FloatField() # imitation targets are weighted by distance to average fitness/firm profit
    prob_imitation_target = models.FloatField() # probability to be imitated
    selected = models.BooleanField() # 1 if this firm selects current manager out
    imitation_target = models.IntegerField() # id of firm who is imitated


class Observations(ExtraModel):
    group = models.Link(Group) # id of group
    player = models.Link(Player) # id of player
    supergame = models.IntegerField() # tracks current supergame
    period = models.IntegerField() # tracks current period
    gamma = models.FloatField() # treatment variable, substitutability between goods 
    confidence = models.FloatField() # document player's confidence in current supergame
    action = models.FloatField() # document player's action in current period
    period_payoff = models.FloatField() # document player's payoff in current period
    period_fitness = models.FloatField() # player's firm's profits in current period
    timestamp = models.FloatField() # timestamp when the data arrived
    expected_timestamp = models.FloatField() # timestamp when the data should have arrived (to track desyncs)
    joint_payoff_info = models.BooleanField() # treatment variable, whether there is additional information on joint payoffs


# PAGES
class Instructions(Page):
    # on the instructions page send some data to the template: number of supergames, number of periods within each supergame, how long each period is (in seconds) and how many points convert to one Euro
    # also, obviously, only display this page in the first supergame, and don't if we are running a simulation
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            num_rounds = C.NUM_ROUNDS,
            num_periods = player.session.config['num_periods'],
            period_length = round(player.session.config['mseconds_per_period']/1000),
            conversion_rate = player.session.config['conversion_rate'],
            joint_payoff_info = player.session.config['joint_payoff_info'],
            participation_fee = player.session.config['participation_fee'],
            )

    def is_displayed(player):
        return player.session.config['simulation'] == False and player.subsession.round_number == 1


class SetupWaitPage(WaitPage):
    # on the waitpage wait for all players in a group, then calculate the payoff and fitness for the first period (which is not paid)
    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()
        for p in players:
            p.timestamp = time.time() * 1000
            p.confidence = p.participant.confidence
            partner = p.get_others_in_group()[0]
            p.period_payoff = payoff_function('payoff', p, partner)
            p.period_fitness = payoff_function('fitness', p, partner)

        # if we are running a simulation, let managers play Nash in all rounds
        if p.session.config['simulation'] == True:
            for p in players:
                partner = p.get_others_in_group()[0]
                p.action = (2*p.confidence - p.group.gamma*partner.confidence)/(4-p.group.gamma*p.group.gamma)
            for p in players:
                partner = p.get_others_in_group()[0]
                p.period_payoff = payoff_function('payoff', p, partner)
                p.period_fitness = payoff_function('fitness', p, partner)

        update_group_vars(group) # use this function to update all the group values after the player variables have all been set
        group.expected_timestamp = max([p.timestamp for p in players])

        for p in players:
            save_period(p) # save data for all players


class Decision(Page):
    @staticmethod
    def vars_for_template(player: Player):
        # if we are in the first period, it is not incentivized, so simply return a period payoff of zero. 
        if player.period == 0:
            period_payoff = float(0)
        else:
            period_payoff = round(player.period_payoff,1)

        # whenever the page is (re)loaded, the current period payoff and the cumulative payoff up to that period are sent to the page
        return dict(
            round_payoff = round(player.round_payoff,1),
            period_payoff = period_payoff,
            period = player.group.period + 1
        )

    # just some variables for javascript
    @staticmethod
    def js_vars(player: Player):
        partner = player.get_others_in_group()[0]
        return dict(
            num_periods = player.session.config['num_periods'],
            p1_action = player.group.p1_action,
            p2_action = player.group.p2_action,
            p1_period_payoff = player.group.p1_period_payoff,
            p2_period_payoff = player.group.p2_period_payoff,
            id = player.id_in_group,
            confidence = player.participant.confidence,
            partner_confidence = partner.participant.confidence,
            number_of_choices = 10**C.ACTION_DECIMAL_PLACES,
            simulation = player.session.config['simulation'],
            gamma = player.group.gamma,
            joint_payoff_info = player.session.config['joint_payoff_info'],
        )

    # we have to work with group variables and not subject variables because of the live page.
    # the logic is as follows: as soon as the page loads, the page sends a signal "ready" to the server.
    # the first client to report "ready" doesn't yield a reply. the server has to wait for the second client first.
    # the period can only start when both are ready.
    # as soon as both members of a group have reported "ready", the server sends a signal to all clients in the group to start the next period
    # this signal contains all information about the current period, actions, payoffs, when the clients should reply, etc.
    # the clients start a period and return a reply after next_period_length milliseconds.
    # now the server again has to wait for the second reply to come back to calculate payoffs.
    # the server compares when the reply came and when the server expected the reply to come.
    # there is a transmission and computational delay, also javascript isn't good at keeping a rhythm.
    # to keep the rhythm the server adjusts the next period's length by the bias.
    # there is a maximum negative adjustment time so if one period is delayed by a very long time, the next period is not of length zero.
    @staticmethod
    def live_method(player: Player, data):
        #print(data) # for debugging purposes
        timestamp = time.time() * 1000 # timestamp in milliseconds
        period_length = player.session.config['mseconds_per_period']
        num_periods = player.session.config['num_periods']
        partner = player.get_others_in_group()[0]
        p1 = player.group.get_player_by_id(1)
        p2 = player.group.get_player_by_id(2)

        if data['type'] == 'ready':
            player.ready = True
            player.timestamp = timestamp

            # if partner is ready and supergame has not started yet, start initial period 0
            if partner.ready and not player.group.supergame_started:
                player.group.supergame_started = True
                return {0: dict(
                    type = 'start-period',
                    period = player.group.period,
                    p1_action = player.group.p1_action,
                    p2_action = player.group.p2_action,
                    p1_period_payoff = player.group.p1_period_payoff,
                    p2_period_payoff = player.group.p2_period_payoff,
                    p1_round_payoff = p1.round_payoff,
                    p2_round_payoff = p2.round_payoff,
                    expected = player.timestamp + period_length,
                    next_period_length = period_length
                    )
                }

            # if all players are ready and the game has already started (ie the page has reloaded) 
            # and the player is not ahead of their partner in periods
            # send start signal with current period info to client who reloaded only
            elif partner.ready and player.group.supergame_started and player.period <= num_periods and player.period <= partner.period: 
                return {player.id_in_group: dict(
                    type = 'start-period',
                    period = player.group.period,
                    p1_action = player.group.p1_action,
                    p2_action = player.group.p2_action,
                    p1_period_payoff = player.group.p1_period_payoff,
                    p2_period_payoff = player.group.p2_period_payoff,
                    p1_round_payoff = p1.round_payoff,
                    p2_round_payoff = p2.round_payoff,
                    expected = player.timestamp + period_length,
                    next_period_length = period_length
                    )}
            # else do nothing and wait

        # if a client sends an update save it to the player variable
        if data['type'] == 'update':
            player.period = player.period + 1
            player.action = data['action']
            player.timestamp = timestamp

            # if partner's action has arrived, calculate payoffs, copy data to group variable, save observation and 
            # send information to everyone in group
            if player.period == partner.period:
                if player.period < num_periods:
                    type = 'start-period'
                else:
                    type = 'end-supergame'

                # update group fields and calculate payoffs
                player.group.period = player.period
                for p in player.group.get_players():
                    partner = p.get_others_in_group()[0]
                    p.period_payoff = payoff_function('payoff', p, partner)
                    p.round_payoff += p.period_payoff
                    p.period_fitness = payoff_function('fitness', p, partner)
                    p.round_fitness += p.period_fitness

                player.group.expected_timestamp = data['expected']
                update_group_vars(player.group)
                for p in player.group.get_players():
                    save_period(p)

                # adjust period length for last period's bias
                dt = timestamp - data['expected']
                next_period_length = max(period_length - player.session.config['max_adjustment'], period_length - dt)

                return {0: dict(
                    type = type,
                    period = player.group.period,
                    p1_action = player.group.p1_action,
                    p2_action = player.group.p2_action,
                    p1_period_payoff = player.group.p1_period_payoff,
                    p2_period_payoff = player.group.p2_period_payoff,
                    p1_round_payoff = p1.round_payoff,
                    p2_round_payoff = p2.round_payoff,
                    expected = timestamp + next_period_length,
                    next_period_length = next_period_length
                    )}


class ResultsWaitPage(WaitPage):
    # on this page convert the points from the previous supergame to Euro
    wait_for_all_groups = True
    def after_all_players_arrive(subsession):
        update_confidence(subsession)
        for p in subsession.get_players():
            p.participant.total_payoff += p.round_payoff
            p.payoff = p.round_payoff / p.session.config['conversion_rate']


class Results(Page):
    def is_displayed(player):
        return player.session.config['simulation'] == False
    
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            round_payoff = round(player.round_payoff,1),
            total_payoff = round(player.participant.total_payoff,1),
        )


page_sequence = [Instructions, SetupWaitPage, Decision, ResultsWaitPage, Results]


# FUNCTIONS
def creating_session(subsession: Subsession):
    # in round 1, assign a player to a population and draw an initial a
    if subsession.round_number == 1:
        for p in subsession.get_players():
            p.participant.population = (p.participant.id_in_session - 1) // C.POPULATION_SIZE + 1
            p.participant.total_payoff = 0
    
    # shuffle the matching within each population every round (and assign initial confidence)
    players = subsession.get_players()
    for p in players:
        p.population = p.participant.population
    num_populations = max([p.population for p in players])
    new_group_matrix = []
    i = 1
    while i <= num_populations:
        population = [p for p in players if p.population == i]
        if subsession.round_number == 1:
            confidence = draw_confidence(subsession)
            for p in population:
                p.participant.confidence = confidence
        random.shuffle(population)
        j = 0
        while j < len(population):
            new_group = [population[j], population[j+1]]
            new_group_matrix.append(new_group)
            j += 2
        i += 1
    subsession.set_group_matrix(new_group_matrix)

    # set the gamma parameter for all groups
    for g in subsession.get_groups():
        g.gamma = subsession.session.config['gamma']

    # draw player's initial action
    for p in subsession.get_players():
        p.population = p.participant.population
        p.action = draw_initial_action()


def draw_confidence(subsession):
    confidence = random.uniform(subsession.session.config['initial_confidence_lower'], subsession.session.config['initial_confidence_upper'])
    return confidence


def draw_initial_action():
    action = round(random.random(),C.ACTION_DECIMAL_PLACES)
    return action


def payoff_function(type, player, partner):
    if type == 'payoff':
        intercept = player.confidence
    elif type == 'fitness':
        intercept = 1
    return player.action * max(0, intercept - player.action - partner.action * player.group.gamma) * 100 # scale up by 100 to have nicer numbers


def update_group_vars(group):
    p1 = group.get_player_by_id(1)
    p2 = group.get_player_by_id(2)
    group.p1_action = p1.action
    group.p2_action = p2.action
    group.p1_period_payoff = p1.period_payoff
    group.p2_period_payoff = p2.period_payoff


# the core function of the study
# 
def update_confidence(subsession):
    players = subsession.get_players()
    num_populations = max([p.population for p in players])
    i = 1
    while i <= num_populations:
        population = [p for p in players if i == p.population]
        pop_fitness = [p.round_fitness for p in population]
        avg_pop_fitness = sum(pop_fitness)/len(pop_fitness)
        # the chance to select one's manager increases linearly from the best-performing (in terms of fitness/profits) to the worst-performing firm
        for p in population:
            p.rank = sum([p.round_fitness < f for f in pop_fitness])
            p.weight = max(0, p.round_fitness - avg_pop_fitness)
        for r in range(len(population)):
            equal_rank = [p for p in population if p.rank == r]
            if len(equal_rank) > 1:
                tiebreaker = list(range(len(equal_rank))) # randomly break ties in ranks
                random.shuffle(tiebreaker)
                for e in range(len(equal_rank)):
                    equal_rank[e].rank = equal_rank[e].rank + tiebreaker[e]
        for p in population:
            p.prob_selection = p.rank/(len(population) - 1)
        
        # if a firm wants a new manager, they choose a target from firms beating the average in the population, weighted by the distance to the average.
        if all(p.weight == 0 for p in population):
            for p in population:
                p.weight = 1
        weightsum = sum([p.weight for p in population])
        for p in population:
            p.prob_imitation_target = p.weight/weightsum
        
        # randomly draw if a firm selects their manager. if they do, add a random uniform error in the target's confidence
        for p in population:
            if random.random() > p.prob_selection:
                p.selected = False
                next_confidence = p.confidence
            else:
                p.selected = True
                imitation_target = random.choices(population, [pl.prob_imitation_target for pl in population])[0]
                p.imitation_target = imitation_target.participant.id_in_session
                next_confidence = imitation_target.confidence + random.uniform(-0.1, 0.1)
            p.participant.confidence = next_confidence
        
        i += 1



def save_period(player):
    Observations.create(
        player = player,
        group = player.group,
        supergame = player.round_number,
        period = player.group.period,
        gamma = player.group.gamma,
        confidence = player.confidence,
        action = player.action,
        period_payoff = player.period_payoff,
        period_fitness = player.period_fitness,
        timestamp = player.timestamp,
        expected_timestamp = player.group.expected_timestamp,
        joint_payoff_info = player.session.config['joint_payoff_info']
        )


def custom_export(players):
    yield [
        'session.code', 
        'participant.id', 
        'participant.code',
        'participant.population',
        'group.id',
        'player.id',
        'player.supergame',
        'player.period',
        'group.gamma',
        'player.confidence',
        'player.action',
        'player.payoff',
        'player.fitness',
        'player.timestamp',
        'player.expected_timestamp',
        'player.joint_payoff_info'
    ]
    for p in players:
        pp = p.participant
        for obs in Observations.filter(player=p):
            yield [
                pp.session.code,
                pp.id_in_session,
                pp.code,
                pp.population,
                p.group.id_in_subsession,
                p.id_in_group,
                obs.supergame,
                obs.period,
                obs.gamma,
                obs.confidence,
                obs.action,
                obs.period_payoff,
                obs.period_fitness,
                obs.timestamp,
                obs.expected_timestamp,
                obs.joint_payoff_info
            ]
