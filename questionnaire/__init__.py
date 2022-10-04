from math import ceil
from otree.api import *

doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'questionnaire'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    gender = models.StringField(
        choices=[
            ['m', 'männlich'],
            ['f', 'weiblich'],
            ['o', 'andere'],
        ],
        label="Gender"
    )
    age = models.IntegerField(min=0, max=100, label="Wie alt sind Sie?")
    field = models.LongStringField(label="Welchen Studiengang studieren sie?")
    semesters = models.IntegerField(min=0, max=100, label="Im wievielten Semester studieren Sie?")
    strategy = models.LongStringField(blank=True,
                                      label="Bitte beschreiben Sie Ihren Gedankengang oder Ihre Strategie in diesem Experiment.")
    comments = models.LongStringField(blank=True,
                                      label="Haben Sie noch andere Kommentare oder Fragen zu diesem Experiment?")

# PAGES
class Questionnaire(Page):
    form_model = "player"
    form_fields = ['gender', 'age', 'field', 'semesters', 'strategy', 'comments']
    # @staticmethod
    # def before_next_page(player: Player, timeout_happened):
    #     player.participant.payoff = ceil(player.participant.payoff * 2) / 2


page_sequence = [Questionnaire]
