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
    NUM_ROUNDS = 60
    POPULATION_SIZE = 6
    ACTION_DECIMAL_PLACES = 3


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    gamma = models.FloatField()  # substitutability
    p1_action = models.FloatField()
    p2_action = models.FloatField()
    p1_period_payoff = models.FloatField()
    p2_period_payoff = models.FloatField()
    expected_timestamp = models.FloatField() # when is the period expected to happen
    period = models.IntegerField(initial=0)
    supergame_started = models.BooleanField(initial=False)


class Player(BasePlayer):
    population = models.IntegerField()
    confidence = models.FloatField()
    action = models.FloatField()
    period_payoff = models.FloatField()
    round_payoff = models.FloatField(initial=0)
    period_fitness = models.FloatField()
    period = models.IntegerField(initial=0)
    timestamp = models.FloatField() # in milliseconds
    round_fitness = models.FloatField(initial=0)
    ready = models.BooleanField(initial=False)
    rank = models.IntegerField()
    prob_selection = models.FloatField()
    weight = models.FloatField()
    prob_imitation_target = models.FloatField()
    selected = models.BooleanField()
    imitation_target = models.IntegerField()


class Observations(ExtraModel):
    group = models.Link(Group)
    player = models.Link(Player)
    supergame = models.IntegerField()
    period = models.IntegerField()
    gamma = models.FloatField()
    confidence = models.FloatField()
    action = models.FloatField()
    period_payoff = models.FloatField()
    period_fitness = models.FloatField()
    timestamp = models.FloatField()
    expected_timestamp = models.FloatField()


# PAGES
class Instructions(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            num_rounds = C.NUM_ROUNDS,
            num_periods = player.session.config['num_periods'],
            period_length = round(player.session.config['mseconds_per_period']/1000),
            conversion_rate = player.session.config['conversion_rate']
            )

    def is_displayed(player):
        return player.session.config['simulation'] == False and player.subsession.round_number == 1


class SetupWaitPage(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()
        for p in players:
            p.timestamp = time.time() * 1000
            p.confidence = p.participant.confidence
            partner = p.get_others_in_group()[0]
            p.period_payoff = payoff_function('payoff', p, partner)
            p.period_fitness = payoff_function('fitness', p, partner)

        if p.session.config['simulation'] == True:
            for p in players:
                partner = p.get_others_in_group()[0]
                p.action = (2*p.confidence - p.group.gamma*partner.confidence)/(4-p.group.gamma*p.group.gamma)
            for p in players:
                partner = p.get_others_in_group()[0]
                p.period_payoff = payoff_function('payoff', p, partner)
                p.period_fitness = payoff_function('fitness', p, partner)

        update_group_vars(group)
        group.expected_timestamp = max([p.timestamp for p in players])

        for p in players:
            save_period(p)


class Decision(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            round_payoff = round(player.round_payoff,1),
            period = player.group.period + 1
        )


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
            simulation = player.session.config['simulation']
        )

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


#page_sequence = [SetupWaitPage, Decision, ResultsWaitPage]
page_sequence = [Instructions, SetupWaitPage, Decision, ResultsWaitPage, Results]


# FUNCTIONS
def creating_session(subsession: Subsession):
    # in round 1, assign a player to a population and draw an initial a
    if subsession.round_number == 1:
        for g in subsession.get_groups():
            confidence = draw_confidence(g)
            for p in g.get_players():
                p.participant.population = (p.participant.id_in_session - 1) // C.POPULATION_SIZE + 1
                p.participant.total_payoff = 0
                p.participant.confidence = confidence

    # draw player's initial action
    for p in subsession.get_players():
        p.population = p.participant.population
        p.action = draw_initial_action()

    # shuffle the matching within each population every round
    players = subsession.get_players()
    num_populations = max([p.population for p in players])
    new_group_matrix = []
    i = 1
    while i <= num_populations:
        population = [p for p in players if p.population == i]
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


def draw_confidence(group):
    confidence = random.uniform(group.session.config['initial_confidence_lower'], group.session.config['initial_confidence_upper'])
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


def update_confidence(subsession):
    players = subsession.get_players()
    num_populations = max([p.population for p in players])
    i = 1
    while i <= num_populations:
        population = [p for p in players if i == p.population]
        pop_fitness = [p.round_fitness for p in population]
        avg_pop_fitness = sum(pop_fitness)/len(pop_fitness)
        for p in population:
            p.rank = sum([p.round_fitness < f for f in pop_fitness])
            p.weight = max(0, p.round_fitness - avg_pop_fitness)
        for r in range(len(population)):
            equal_rank = [p for p in population if p.rank == r]
            if len(equal_rank) > 1:
                tiebreaker = list(range(len(equal_rank)))
                random.shuffle(tiebreaker)
                for e in range(len(equal_rank)):
                    equal_rank[e].rank = equal_rank[e].rank + tiebreaker[e]
        for p in population:
            p.prob_selection = p.rank/(len(population) - 1)
        if all(p.weight == 0 for p in population):
            for p in population:
                p.weight = 1
        weightsum = sum([p.weight for p in population])
        for p in population:
            p.prob_imitation_target = p.weight/weightsum
        
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
        expected_timestamp = player.group.expected_timestamp
    )


def custom_export(players):
    yield [
        'session.code', 
        'participant.id', 
        'participant.code', 
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
        'player.expected_timestamp'
    ]
    for p in players:
        pp = p.participant
        for obs in Observations.filter(player=p):
            yield [
                pp.session.code,
                pp.id_in_session,
                pp.code,
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
                obs.expected_timestamp
            ]
