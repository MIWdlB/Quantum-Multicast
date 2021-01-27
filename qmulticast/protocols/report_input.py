"""Protocol to look at a single port and report when it gets input."""

from netsquid.components.protocols import NodeProtocol

class InputThenDo(NodeProtocol):
    """Class to watch for any change to the memory."""