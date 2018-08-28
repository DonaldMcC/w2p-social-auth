import sys

#FIXME: Hack to social.utils.import_module() work
from plugin_social_auth import w2p_strategy, models, utils, pipeline
#from plugin_social_auth import w2p_strategy
#from plugin_social_auth import models
#from plugin_social_auth import utils
#from plugin_social_auth import pipeline

sys.modules['plugin_social_auth.w2p_strategy'] = w2p_strategy
sys.modules['plugin_social_auth.models'] = models
sys.modules['plugin_social_auth.utils'] = utils
sys.modules['plugin_social_auth.pipeline'] = pipeline

