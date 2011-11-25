
class InvalidMessage(RuntimeError):
    """
    Raised if message is missing vital headers, such
    as recipients or sender address.
    """

class BadHeaders(RuntimeError): 
    """
    Raised if message contains newlines in headers.
    """
