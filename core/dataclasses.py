from django.http import HttpRequest
from dataclasses import dataclass, field
from typing import Dict, List  # For Python < 3.9
from enum import Enum
import json

class Gamemodes(Enum):
    MEME_FORGE = "MemeForge"

    def get_class(value):
        """
        Returns the Gamemode dataclass pertaining to the given Enum.
        """
        if value == Gamemodes.MEME_FORGE:
            return MemeForge
        else:
            return None

class TemplateTags(Enum):
    NSFW = "NSFW"
    ANIMATED = "animated"

@dataclass
class GuestUser():
    """
    Schema for GuestUser.
    """
    username:str
    profile_picture:str

    @staticmethod
    def is_valid_guest_user(request:HttpRequest=None, username:str=None, profile_picture:str=None) -> bool:
        """
        Returns true if the given parameters make for a valid guest user.
        """
        if username and profile_picture and not request:
            return True
        else:
            return "username" in request.session and "profile_picture" in request.session

    def is_valid(self) -> bool:
        """
        Returns true if self is a valid guest user.
        """
        return self.is_valid_guest_user(username=self.username, profile_picture=self.profile_picture)

    def save_guest_user_to_session(self, request:HttpRequest):
        """
        Saves self to the given requests' session.
        """
        request.session["username"] = self.username
        request.session["profile_picture"] = self.profile_picture

    @staticmethod
    def get_guest_user_from_session(request:HttpRequest):
        """
        Gets the guest user from the given requests' session.
        """
        return GuestUser(
            username =  request.session["username"],
            profile_picture = request.session["profile_picture"]
        )

@dataclass
class Gamemode:
    """
    Parent schema for gamemode configuration.
    """
    key: str
    rounds: int

    def serialize(self):
        """
        Converts a gamemode instance to a JSON string.
        """
        return json.dumps(self.__dict__)

    def deserialize(data):
        """
        Converts a JSON string back into a gamemode instance.
        """
        return Gamemode(**json.loads(data))

    def deserialize(data):
        """
        Converts a JSON string back into a gamemode instance.
        """
        return Gamemode(**json.loads(data))

    @classmethod
    def get_settings() -> Dict[str, str]:
        """
        This function should return a datastructure defining all settings a host can set for the particular gamemode.
        Subclasses should override this to handle gamemode-specific fields.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @classmethod
    def from_form_data(cls, data: Dict) -> "Gamemode":
        """
        Converts form data into a valid Gamemode instance.
        Subclasses should override this to handle gamemode-specific fields.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @classmethod
    def from_post_request(cls, request:HttpRequest) -> "Gamemode":
        """
        Converts form data into a valid MemeForge instance.
        """
        return cls.from_form_data(request.POST)

@dataclass
class MemeForge(Gamemode):
    """
    Schema for MemeForge gamemode.
    """
    # Class-level constants
    TEXT_INPUT_CONSTRAINTS = {"max_length": 100}
    TIME_LIMIT_VOTING = 30

    DEFAULT_ROUNDS = 3
    MIN_ROUNDS = 1
    MAX_ROUNDS = 10

    DEFAULT_TIME_LIMIT = 180
    MIN_TIME_LIMIT = 60
    MAX_TIME_LIMIT = 600

    DEFAULT_REROLLS = 5
    MIN_REROLLS = 0
    MAX_REROLLS = 10

    DEFAULT_TEMPLATE_CONSTRAINTS = {"tags": []}

    rounds: int
    time_limit_rounds: int
    rerolls_per_player: int
    template_constraints: Dict[str, List[str]]

    def __init__(self,rounds:int, time_limit_rounds:int, rerolls_per_player:int, template_constraints: Dict[str, List[str]]):
        self.key = Gamemodes.MEME_FORGE.name.lower()
        self.rounds = rounds
        self.time_limit_rounds = time_limit_rounds
        self.rerolls_per_player = rerolls_per_player
        self.template_constraints = template_constraints

    @classmethod
    def get_settings(cls) -> Dict:
        """
        Returns a datastructure defining all settings a host can set for the particular gamemode.
        """
        return {
            "key": Gamemodes.MEME_FORGE.name.lower(),
            "name": Gamemodes.MEME_FORGE.value,
            "settings": [
                {"key": "rounds", "label": "Number of Rounds", "type": "number", "default": cls.DEFAULT_ROUNDS, "min": cls.MIN_ROUNDS, "max":  cls.MAX_ROUNDS},
                {"key": "time_limit", "label": "Time Limit per Round (Seconds)", "type": "number", "default": cls.DEFAULT_TIME_LIMIT, "min":  cls.MIN_TIME_LIMIT, "max": cls.MAX_TIME_LIMIT},
                {"key": "rerolls", "label": "Rerolls Per Player", "type": "number", "default": cls.DEFAULT_REROLLS, "min":  cls.MIN_REROLLS, "max": cls.MAX_REROLLS},
                {"key": "template_tags", "label": "Template Tags", "type": "select", "multiple": True, "default": cls.DEFAULT_TEMPLATE_CONSTRAINTS, "options": [
                    {"value": tag.value, "label": tag.name.replace("_", " ").title()} for tag in TemplateTags
                ]}
            ]
        }

    @classmethod
    def from_form_data(cls, data: Dict) -> "MemeForge":
        """
        Converts form data into a valid MemeForge instance.
        """
        return cls(
            rounds=int(data.get("rounds", cls.DEFAULT_ROUNDS)),
            time_limit_rounds=int(data.get("time_limit", cls.DEFAULT_TIME_LIMIT)),
            rerolls_per_player=int(data.get("rerolls", cls.DEFAULT_REROLLS)),
            template_constraints={"tags": data.getlist("template_tags", [])}
        )

@dataclass
class Lobby:
    """
    Schema for lobby state.
    """
    code: str
    creator: str
    participants: List[str] = field(default_factory=list)
    game_started: bool = False
    gamemode: Gamemode = None
    settings: Dict = field(default_factory=dict)

    def serialize(self):
        """
        Converts a lobby instance to a JSON string.
        """
        return json.dumps(self.__dict__, default=self._serialize_custom_objects)

    @staticmethod
    def _serialize_custom_objects(obj):
        """
        Handles custom object serialization.
        """
        if hasattr(obj, "__dict__"):
            return obj.__dict__  # Convert objects with __dict__ to dictionaries
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()  # Use to_dict if available
        else:
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    @staticmethod
    def deserialize(data):
        """
        Converts a JSON string back into a lobby instance.
        """
        return Lobby(**json.loads(data))
