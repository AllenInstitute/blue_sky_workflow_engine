from circus.plugins import CircusPlugin


class CircusLogger(CircusPlugin):
    name = 'circus_logger'

    def __init__(self, *args, **config):
        super(CircusLogger, self).__init__(*args, **config)
        self.filename = config.get('filename')
        self.file = None

    def handle_init(self):
        self.file = open(self.filename, 'a+', buffering=1)

    def handle_stop(self):
        self.file.close()

    def handle_recv(self, data):
        watcher_name, action, msg = self.split_data(data) 
        msg_dict = self.load_message(msg)
        #self.file.write('%s::%s::%r\n' % (action, watcher_name, msg_dict))
        print('%s::%s::%r\n' % (action, watcher_name, msg_dict))

