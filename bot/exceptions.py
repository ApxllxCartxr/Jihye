from disnake import DiscordException


class ExistingEntry(DiscordException):
    """An entry was already found in the cache with this key."""


class NonExistentEntry(DiscordException):
    """No entry found in the cache with this key."""

