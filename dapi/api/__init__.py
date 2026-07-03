"""API submodules for Dapi."""
from .messages import MessagesAPI
from .users import UsersAPI
from .guilds import GuildsAPI
from .channels import ChannelsAPI
from .reactions import ReactionsAPI
from .relationships import RelationshipsAPI
from .presence import PresenceAPI
from .misc import MiscAPI
from .attachments import AttachmentsAPI

__all__ = [
    'MessagesAPI',
    'UsersAPI',
    'GuildsAPI',
    'ChannelsAPI',
    'ReactionsAPI',
    'RelationshipsAPI',
    'PresenceAPI',
    'MiscAPI',
    'AttachmentsAPI',
]
