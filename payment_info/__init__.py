from os import stat
from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'payment_info'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


# PAGES
class PaymentInformation(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            total_payoff = round(player.participant.total_payoff,1),
        )


class GoodBye(Page):
    pass


page_sequence = [PaymentInformation, GoodBye]
