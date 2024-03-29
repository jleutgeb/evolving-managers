from os import environ

SESSION_CONFIGS = [
    dict(
        name='evolving_managers_demo',
        app_sequence=['consent', 'evolving_managers', 'questionnaire', 'payment_info'],
        num_demo_participants = 2,
        simulation = False, # if simulated, the program will just play the best-reply
        conversion_rate = 1000, # how many points for 1 Euro
        participation_fee = 6.0,
        treatment_file = 'demo.csv',
    ),
    dict(
        name='evolving_managers_baseline',
        app_sequence=['consent', 'evolving_managers', 'questionnaire', 'payment_info'],
        num_demo_participants = 2,
        simulation = False, # if simulated, the program will just play the best-reply
        conversion_rate = 1000, # how many points for 1 Euro
        participation_fee = 6.0,
        treatment_file = 'baseline.csv',
    ),
    dict(
        name='evolving_managers_joint',
        app_sequence=['consent', 'evolving_managers', 'questionnaire', 'payment_info'],
        num_demo_participants = 2,
        simulation = False, # if simulated, the program will just play the best-reply
        conversion_rate = 1000, # how many points for 1 Euro
        participation_fee = 6.0,
        treatment_file = 'joint.csv',
    ),
    dict(
        name='evolving_managers_relative',
        app_sequence=['consent', 'evolving_managers', 'questionnaire', 'payment_info'],
        num_demo_participants = 2,
        simulation = False, # if simulated, the program will just play the best-reply
        conversion_rate = 1000, # how many points for 1 Euro
        participation_fee = 6.0,
        treatment_file = 'relative.csv',
    ),
]

ROOMS = [
    dict(
        name = 'TU_LAB',
        display_name = 'TU Lab',
        participant_label_file = '_rooms/TU_lab.txt',
        use_secure_urls = False,
    ),
    dict(
        name = 'TU_LAB_noIDs',
        display_name = 'TU Lab no IDs',
    ),
]


# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = [
     'confidence',
     'population',
     'total_payoff',
     'configs'
]
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'de'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = False

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '3117637993201'
