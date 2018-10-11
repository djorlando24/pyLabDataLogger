"""
message - Simple class to make construction and decoding of message bytes
easier. Based on APT Communication Protocol Rev. 14 (Thorlabs)
"""

import struct as st
from collections import namedtuple


"""Define available messages"""
MGMSG_HEADER_SIZE                  = 6

# Generic Commands
MGMSG_MOD_IDENTIFY                 = 0x0223
MGMSG_HW_RESPONSE                  = 0x0080

MGMSG_HW_REQ_INFO                  = 0x0005
MGMSG_HW_GET_INFO                  = 0x0006

MGMSG_MOT_ACK_DCSTATUSUPDATE       = 0x0492

# Motor Commands
MGMSG_MOT_SET_PZSTAGEPARAMDEFAULTS = 0x0686

MGMSG_MOT_MOVE_HOME                = 0x0443
MGMSG_MOT_MOVE_HOMED               = 0x0444
MGMSG_MOT_MOVE_ABSOLUTE            = 0x0453
MGMSG_MOT_MOVE_COMPLETED           = 0x0464

MGMSG_MOT_SET_HOMEPARAMS           = 0x0440
MGMSG_MOT_REQ_HOMEPARAMS           = 0x0441
MGMSG_MOT_GET_HOMEPARAMS           = 0x0442

MGMSG_MOT_REQ_POSCOUNTER           = 0x0411
MGMSG_MOT_GET_POSCOUNTER           = 0x0412

MGMSG_MOT_REQ_DCSTATUSUPDATE       = 0x0490
MGMSG_MOT_GET_DCSTATUSUPDATE       = 0x0491

MGMSG_MOT_SET_VELPARAMS            = 0x413
MGMSG_MOT_REQ_VELPARAMS            = 0x414
MGMSG_MOT_GET_VELPARAMS            = 0x415

MGMSG_MOT_SUSPEND_ENDOFMOVEMSGS    = 0x046B
MGMSG_MOT_RESUME_ENDOFMOVEMSGS     = 0x046C

MGMSG_MOT_MOVE_STOP                = 0x0465
MGMSG_MOT_MOVE_STOPPED             = 0x0466





_Message = namedtuple('_Message', ['messageID'
                                  ,'param1'
                                  ,'param2'
                                  ,'dest'
                                  ,'src'
                                  ,'data'
                                  ])





class Message(_Message):
    """Basic message class extending a namedtuple
    """

    @classmethod
    def unpack(cls, databytes, header_only=False):
        """Unpack a bytestring to a message object

        pack() produces a string of bytes from a Message, unpack() produces a
        Message from a string of bytes

        If header_only is True, then we will only attempt to decode the header,
        ignoring any bytes that follow, if any. This allows you get determine
        what the message is without having to read it in its entirety.

        Note that dest is returned AS IS, which means its MSB will be set if
        the message is more than just a header.

        Args:
            databytes (bytestring): string of bytes to unpack
            header_only (bool): header only unpacking ignoring the data part

        Returns:
            Message: Message instance of unpacked bytestring
        """

        Header = namedtuple('Header', ['messageID'
                                      ,'param1'
                                      ,'param2'
                                      ,'dest'
                                      ,'src'
                                      ])

        hd = Header._make(st.unpack('<HBBBB',databytes[:6]))

        # if MSB of dest is set, then there is additional data to follow
        if hd.dest & 0x80:
            datalen = hd.param1 | (hd.param2<<8)

            if header_only:
                data=None
            else:
                data=st.unpack('<%dB'%(datalen), databytes[6:])

            return Message( hd.messageID,
                            dest   = hd.dest,
                            src    = hd.src,
                            param1 = hd.param1,
                            param2 = hd.param2,
                            data   = data)
        else:
            return Message( hd.messageID,
                            param1 = hd.param1,
                            param2 = hd.param2,
                            dest   = hd.dest,
                            src    = hd.src)


    def __new__(cls, messageID, dest=0x50, src=0x01, param1=0, param2=0, data=None):
        """Constructor

        Args:
            messageID (int): integer message ID
            dest (byte): destination device address
            src (byte): source device address
            param1 (int): integer parameter1
            param2 (int): integer parameter2
            data (bytes): data block bytestring

        Returns:
            Message: instance of Message class
        """

        assert type(messageID) == int, 'messageID is not an integer value'

        if data:
            assert (param1 == 0 and param2 == 0), 'param1 or param2 not zero'
            assert type(data) == bytes, 'data is of type %s. should be <bytes>' % type(data)
            #assert type(data) in [list, tuple, str]     # original version
   
            if type(data) == str:
                data = [ord(c) for c in data]
   
            return super(Message, cls).__new__(Message,
                                               messageID,
                                               None,
                                               None,
                                               dest,
                                               src,
                                               data)
        else:
            assert type(param1) == int , 'param1 is not an integer value'
            assert type(param2) == int , 'param2 is not an integer value'  
            return super(Message, cls).__new__(Message,
                                               messageID,
                                               param1,
                                               param2,
                                               dest,
                                               src,
                                               None)
   

    def pack(self, verbose=False):
        """Pack a message object to the corresponding bytestring

        pack() produces a string of bytes from a Message, unpack() produces a
        Message from a string of bytes

        Args:
            verbose (bool): print resulting bytestring before returning

        Returns:
            bytes: the byte string representing the message
        """

        if self.data:
            """
            <: little endian
            H: 2 bytes for message ID
            H: 2 bytes for data length
            B: unsigned char for dest
            B: unsigned char for src
            %dB: %d bytes of data
            """
            datalen = len(self.data)
            if type(self.data) == str:
                datalist = list(self.data)
            else:
                datalist = self.data
   
            ret = st.pack('<HHBB%dB'%(datalen),
                          self.messageID,
                          datalen,
                          self.dest|0x80,
                          self.src,
                          *datalist)
        else:
            """
            <: little endian
            H: 2 bytes for message ID
            B: unsigned char for param1
            B: unsigned char for param2
            B: unsigned char for dest
            B: unsigned char for src
            """
            ret = st.pack('<HBBBB',
                          self.messageID,
                          self.param1,
                          self.param2,
                          self.dest,
                          self.src)
        if verbose:
            print(bytes(self),'=',map(lambda x:hex(ord(x)), ret))
   
        return ret
   

    def __eq__(self, other):
        """Overwrite =operator
   
        We don't compare the underlying namedtuple because we consider data of
        [1,2,3,4,5] and (1,2,3,4,5) to be the same, while python doesn't.
   
        Args:
            other (Message): comparand message object
   
        Returns:
            bool: =operator result
        """
   
        return self.pack() == other.pack()


    @property
    def datastring(self):
        """Data block of the message

        Returns:
            bytes: data part of message bytestring 
        """

        if type(self.data) == str:
            return bytes(self.data).encode('latin-1')
        else:
            return bytes(''.join(chr(x) for x in self.data)).encode('latin-1')


    @property
    def datalength(self):
        """Length of the message data block

        Returns:
            int: length of message data block::
                -1: no data block
                >0: data length
        """

        if self.hasdata:
            if self.data:
                return len(self.data)
            else:
                return self.param1 | (self.param2<<8)
        else:
            return -1


    @property
    def hasdata(self):
        """Indicates if message has data?

        So far unclear, maybe better look into the APT protocol specification.
        """

        return self.dest & 0x80

