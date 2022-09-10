
class Timed:
    
    class Config(object):
        JOBS = [
        {
            'id': 'update_state',
            'func': 'auction_utils:task',
            'args': (1, 2),
            'trigger': 'cron',
            'day': '*',
            'hour': '13',
            'minute': '16',
            'second': '20'
        },
        {
            
        }
    ]
    SCHEDULER_API_ENABLED = True