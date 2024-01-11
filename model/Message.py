class Message:
    correlation_id = None
    content = None

    def __init__(self, correlation_id, content):
        self.content = content
        self.correlation_id = correlation_id
