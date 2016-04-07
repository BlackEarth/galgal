
from . import Model

class Subscription(Model):
    relation = 'subscriptions'
    pk_fields = ['member', 'kind_id']

class SubscriptionType(Model):
    relation = 'subscription_kinds'
    pk_fields = ['id']

