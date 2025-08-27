from discord import DiscordException


class ExistingEntry(DiscordException):
    """An entry was already found in the cache with this key."""


class NonExistentEntry(DiscordException):
    """No entry found in the cache with this key."""


class PrefixNotFound(DiscordException):
    """No prefix was found for this guild."""


class TaskExists(DiscordException):
    """Task already exists"""


class ReactionExists(DiscordException):
    """Reaction role exists"""


class ReactionDoesNotExists(DiscordException):
    """Reaction role exists"""


class TaskDoesNotExist(DiscordException):
    """Task does not exist"""


class InvalidSetting(DiscordException):
    """Setting does not exist"""


class ARDoesNotExist(DiscordException):
    """Setting does not exist"""


class TriggerExists(DiscordException):
    """Trigger already exists"""


class TriggerDoesNotExist(DiscordException):
    """Trigger does not exist"""


class EmbedDoesNotExist(DiscordException):
    """THe embed does not exitst"""


class EmbedExists(DiscordException):
    """The embed already exists"""
