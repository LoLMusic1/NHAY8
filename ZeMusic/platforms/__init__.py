try:
    from .Apple import AppleAPI
    Apple = AppleAPI()
except ImportError:
    Apple = None

try:
    from .Carbon import CarbonAPI
    Carbon = CarbonAPI()
except ImportError:
    Carbon = None

try:
    from .Resso import RessoAPI  
    Resso = RessoAPI()
except ImportError:
    Resso = None

try:
    from .Soundcloud import SoundAPI
    SoundCloud = SoundAPI()
except ImportError:
    SoundCloud = None

try:
    from .Spotify import SpotifyAPI
    Spotify = SpotifyAPI()
except ImportError:
    Spotify = None

try:
    from .Telegram import TeleAPI
    Telegram = TeleAPI()
except ImportError:
    Telegram = None

try:
    from .Youtube import YouTubeAPI
    YouTube = YouTubeAPI()
except ImportError:
    YouTube = None
