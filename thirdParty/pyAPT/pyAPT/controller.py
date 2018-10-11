"""
controller - Simple class encapsulating an APT controller
"""

import pylibftdi
import time
import struct as st

from .message import Message
from . import message



class OutOfRangeError(Exception):
    """Exception raised when motion destination outside allowed range requested
    """

    def __init__(self, requested, allowed):
        """Constructor

        Args:
            requested (float): destination requested
            allowed (tuple(float,float)): allowed range of stage
        """

        val = '%f requested, but allowed range is %.2f..%.2f' \
            % (requested, allowed[0], allowed[1])
        super(OutOfRangeError, self).__init__(val)





class Controller(object):
    """Device Controller class communicating with the device
    """

    def __init__(self, serial_number=None, label=None):
        """Constructor
        
        Args:
            serial_number (str): S/N of the device
            label (str): optional name of the device
        """

        super(Controller, self).__init__()
   
        dev = pylibftdi.Device(mode='b', device_id=serial_number)
        dev.baudrate = 115200
    
        def _checked_c(ret):
            if not ret == 0:
                raise Exception(dev.ftdi_fn.ftdi_get_error_string())
    
        _checked_c(dev.ftdi_fn.ftdi_set_line_property(8, # number of bits
                                                      1, # number of stop bits
                                                      0  # no parity
                                                      ))
        time.sleep(50.0/1000)
        dev.flush(pylibftdi.FLUSH_BOTH)
        time.sleep(50.0/1000)

        # skipping reset part since it looks like pylibftdi does it already

        # this is pulled from ftdi.h
        SIO_RTS_CTS_HS = (0x1 << 8)
        _checked_c(dev.ftdi_fn.ftdi_setflowctrl(SIO_RTS_CTS_HS))
        _checked_c(dev.ftdi_fn.ftdi_setrts(1))

        self.serial_number = serial_number
        self.label         = label
        self._device       = dev

        # some conservative limits
        self.max_velocity     = 0.3     # mm/s
        self.max_acceleration = 0.3     # mm/s/s

        # these define how encode count translates into position, velocity
        # and acceleration. e.g. 1 mm is equal to 1 * self.position_scale
        # these are set to None on purpose - you should never use this class
        # as is.
        self.position_scale     = None
        self.velocity_scale     = None
        self.acceleration_scale = None

        # defines the linear, i.e. distance, range of the controller
        # unit is in mm
        self.linear_range = (0,10)

        # whether or not sofware limit in position is applied
        self.soft_limits = True

        # the message queue are messages that are sent asynchronously. For
        # example if we performed a move, and are waiting for move completed
        # message, any other message received in the mean time are place in the
        # queue.
        self.message_queue = []


    def __enter__(self):
        return self
   

    def __exit__(self, type_, value, traceback):
        self.close()
   

    def __del__(self):
        self.close()
   

    def __repr__(self):
        return 'Controller(serial=%s, device=%s)' \
            % (self.serial_number, self._device)


    def close(self):
        """Close the device connection
        
        Make the device stop and close the connection
        """
        if not self._device.closed:
            print('Closing connnection to controller: ',self.serial_number)
            self.stop(wait=False)
            # XXX we might want a timeout here, or this will block forever
            self._device.close()
   

    def _send_message(self, m):
        """Send a Message object to device

        Args:
            m (Message): Message object with pack method returning a bytestring
        """
        self._device.write(m.pack())
   

    def _read(self, length, block=True):
        """Read a bytestring string from device

        If block is True, this returns only when the requested number of bytes
        is read. Otherwise we will perform a read, then immediately return with
        however many bytes we managed to read.
     
        Note that if no data is available, then an empty byte string will be
        returned.

        Args:
            lenght (int): requested number of bytes to read
            block (bool): block until requested number of bytes has been read

        Returns:
            bytes: bytestring read from device
        """

        data = bytes()

        while len(data) < length:
            diff = length - len(data)
            data += self._device.read(diff)
            if not block:
                break
     
            time.sleep(0.001)
     
        return data
   

    def _read_message(self):
        """Read a Message from device

        Perform a read operation from device and unpack the bytestring to a
        Message object

        Returns:
            Message: Message object read from device
        """

        data = self._read(message.MGMSG_HEADER_SIZE)
        msg  = Message.unpack(data, header_only=True)

        if msg.hasdata:
            data = self._read(msg.datalength)
            msglist = list(msg)
            msglist[-1] = data
            return Message._make(msglist)

        return msg
   

    def _wait_message(self, expected_messageID):
        """Wait for a specific message from device

        Keep reading messages from device until the expected one is recieved.
        Add all intermediate message to the message_queue.

        Args:
            expected_messageID (int): message ID of expected message

        Returns:
            Message: Message object read from device
        """

        found = False
        while not found:
            m     = self._read_message()
            found = m.messageID == expected_messageID
            if found:
                return m
            else:
                self.message_queue.append(m)
   

    def _position_in_range(self, absolute_pos_mm):
        """Check if position is within range

        Returns True if requested absolute position is within range, False
        otherwise

        Args:
            absolute_pos_mm (float): position on absolute scale to check

        Returns:
            bool: result of the position check
        """

        # get rid of floating point artifacts below our resolution
        enccnt = int(absolute_pos_mm * self.position_scale)
        absolute_pos_mm = enccnt / self.position_scale
    
        if absolute_pos_mm < self.linear_range[0]:
            return False
    
        if absolute_pos_mm > self.linear_range[1]:
            return False
    
        return True
   

    def status(self, channel=1):
        """Return the status of the controller

        Returns the status of the controller, which is its position, velocity,
        and statusbits. Position and velocity will be in mm and mm/s
        respectively.

        Args:
            channel (int): channel of device (multi-channel controllers only)

        Returns:
            ControllerStatus: instance of ControllerStatus
        """
        reqmsg = Message(message.MGMSG_MOT_REQ_DCSTATUSUPDATE, param1=channel)
        self._send_message(reqmsg)
     
        getmsg = self._wait_message(message.MGMSG_MOT_GET_DCSTATUSUPDATE)
        return ControllerStatus(self, getmsg.datastring)
   

    def identify(self):
        """Flashes the controller's activity LED
        """
        idmsg = Message(message.MGMSG_MOD_IDENTIFY)
        self._send_message(idmsg)


    def reset_parameters(self):
        """Resets all parameters to their EEPROM default values.
      
        IMPORTANT: only one class of controller appear to support this at the
        moment, that being the BPC30x series.
        """
        resetmsg = Message(message.MGMSG_MOT_SET_PZSTAGEPARAMDEFAULTS)
        self._send_message(resetmsg)
   

    def request_home_params(self):
        """Read the homing parameters from device

        The homing parameters are encoded in the following way:

        <: little endian
        H: 2 bytes for channel id
        H: 2 bytes for home direction
        H: 2 bytes for limit switch
        i: 4 bytes for homing velocity
        i: 4 bytes for offset distance

        Returns:
            tuple: homing parameters as tuple
        """
        reqmsg = Message(message.MGMSG_MOT_REQ_HOMEPARAMS)
        self._send_message(reqmsg)
   
        getmsg = self._wait_message(message.MGMSG_MOT_GET_HOMEPARAMS)
        dstr = getmsg.datastring
   
        return st.unpack('<HHHii', dstr)
   

    def suspend_end_of_move_messages(self):
        """Send the SUSPEND_ENDOFMOVEMSGS message

        Sent to disable all unsolicited end of move messages and error messages
        returned by the controller, i.e.

            MGMSG_MOT_MOVE_STOPPED
            MGMSG_MOT_MOVE_COMPLETED
            MGMSG_MOT_MOVE_HOMED
        """
        suspendmsg = Message(message.MGMSG_MOT_SUSPEND_ENDOFMOVEMSGS)
        self._send_message(suspendmsg)
   

    def resume_end_of_move_messages(self):
        """Send the RESUME_ENDOFMOVEMSGS message

        Sent to resume all unsolicited end of move messages and error messages
        returned by the controller, i.e.

            MGMSG_MOT_MOVE_STOPPED
            MGMSG_MOT_MOVE_COMPLETED
            MGMSG_MOT_MOVE_HOMED

        The command also disables the error messages that the controller sends
        when an error conditions is detected:

            MGMSG_HW_RESPONSE
            MGMSG_HW_RICHRESPONSE

        This is the default state when the controller is powered up.
        """
        resumemsg = Message(message.MGMSG_MOT_RESUME_ENDOFMOVEMSGS)
        self._send_message(resumemsg)
   

    def home(self, wait=True, velocity=None, offset=0):
        """Move stage to home position

        Args:
            wait (bool): When wait is true, this method doesn't return until
                         MGMSG_MOT_MOVE_HOMED is received. Otherwise it returns
                         immediately after having sent the message.

            velocity (float): When velocity is not None, homing parameters will
                              be set so homing velocity will be as given, in mm
                              per second.
   
            offset (float): offset is the home offset in mm, which will be
                            converted to APT units and passed to the controller
   
        Returns:
            ControllerStatus: only in case ''wait'' is True, None otherwise
        """
   
        # first get the current settings for homing. We do this because despite
        # the fact that the protocol spec says home direction, limit switch,
        # and offset distance parameters are not used, they are in fact
        # significant. If I just pass in 0s for those parameters when setting
        # homing parameter the stage goes the wrong way and runs itself into
        # the other end, causing an error condition.
        #
        # To get around this, and the fact the correct values don't seem to be
        # documented, we get the current parameters, assuming they are correct,
        # and then modify only the velocity and offset component, then send it
        # back to the controller.

        # make sure we never exceed the limits of our stage
        offset = min(offset, self.linear_range[1])
        offset = max(offset, 0)
        offset_apt = offset*self.position_scale
   
        # <: little endian
        # H: 2 bytes for channel id
        # H: 2 bytes for home direction
        # H: 2 bytes for limit switch
        # i: 4 bytes for homing velocity
        # i: 4 bytes for offset distance
        curparams = list(self.request_home_params())
   
        if velocity:
            velocity = min(velocity, self.max_velocity)
            curparams[-2] = int(velocity*self.velocity_scale)
   
        curparams[-1] = offset_apt
   
        newparams= st.pack( '<HHHii',*curparams)
   
        homeparamsmsg = Message(message.MGMSG_MOT_SET_HOMEPARAMS
                               ,data = newparams
                               )
        self._send_message(homeparamsmsg)
   
        if wait:
            self.resume_end_of_move_messages()
        else:
            self.suspend_end_of_move_messages()
   
        homemsg = Message(message.MGMSG_MOT_MOVE_HOME)
        self._send_message(homemsg)
   
        if wait:
            self._wait_message(message.MGMSG_MOT_MOVE_HOMED)
            return self.status()

   
    def position(self, channel=1, raw=False):
        """Get the stage position.

        Args:
            channel (int): channel of device (multi-channel controllers only)
            raw (bool): If True do not convert position to SI unit scale

        Returns:
            position (float): position of stage in mm or enccnts
        """
        reqmsg = Message(message.MGMSG_MOT_REQ_POSCOUNTER, param1=channel)
        self._send_message(reqmsg)
      
        getmsg = self._wait_message(message.MGMSG_MOT_GET_POSCOUNTER)
        dstr = getmsg.datastring
      
        # <: little endian
        # H: 2 bytes for channel id
        # i: 4 bytes for position
        chanid,pos_apt=st.unpack('<Hi', dstr)
      
        if not raw:
          return 1.0*pos_apt / self.position_scale
        else:
          return pos_apt
   

    def goto(self, abs_pos_mm, channel=1, wait=True):
        """Move the stage to an absolute position

        Tells the stage to goto the specified absolute position, in mm.

        Note that the wait is implemented by waiting for
        ``MGMSG_MOT_MOVE_COMPLETED``, then querying status until the position
        returned matches the requested position, and velocity is zero

        Args:
            abs_pos_mm (float): absolute position to goto in mm
            channel (int): channel of device (multi-channel controllers only)
            wait (bool): When wait is True, this method only returns when the
                         stage has signaled that it has finished moving.

        Returns:
            ControllerStatus: only if wait is true, None otherwise

        Raises:
            OutOfRangeError: if abs_pos_mm is outside self.linear_range
        """
   
        if self.soft_limits and not self._position_in_range(abs_pos_mm):
            raise OutOfRangeError(abs_pos_mm, self.linear_range)
   
        abs_pos_apt = int(abs_pos_mm * self.position_scale)
   
        # <: little endian
        # H: 2 bytes for channel id
        # i: 4 bytes for absolute position
        params = st.pack( '<Hi', channel, abs_pos_apt)
   
        if wait:
            self.resume_end_of_move_messages()
        else:
            self.suspend_end_of_move_messages()
   
        movemsg = Message(message.MGMSG_MOT_MOVE_ABSOLUTE, data=params)
        self._send_message(movemsg)
   
        if wait:
            #msg = self._wait_message(message.MGMSG_MOT_MOVE_COMPLETED)
            while True:
                msg = self._read_message()
                if msg.messageID == message.MGMSG_MOT_MOVE_STOPPED \
                        or msg.messageID == message.MGMSG_MOT_MOVE_COMPLETED:
                    break
            sts = ControllerStatus(self, msg.datastring)
            # I find sometimes that after the move completed message there is
            # still some jittering. This aims to wait out the jittering so we
            # are stationary when we return
            while sts.velocity_apt:
                time.sleep(0.01)
                sts = self.status()
            return sts
        else:
            return None
   

    def move(self, dist_mm, channel=1, wait=True):
        """Move the stage to a relative position

        Tells the stage to move from its current position the specified
        distance, in mm
   
        This is currently implemented by getting the current position, then
        computing a new absolute position using dist_mm, then calls goto() and
        returns it returns. Check documentation for goto() for return values
        and such.

        Args:
            dist_mm (float): relative distance to move in mm
            channel (int): channel of device (multi-channel controllers only)
            wait (bool): When wait is True, this method only returns when the
                         stage has signaled that it has finished moving.

        Returns:
            ControllerStatus: only if wait is true, None otherwise

        Raises:
            OutOfRangeError: if abs_pos_mm is outside self.linear_range
        """

        curpos = self.position()
        newpos = curpos + dist_mm

        return self.goto(newpos, channel=channel, wait=wait)
   

    def set_soft_limits(self, soft_limits):
        """Sets whether range limits are observed in software.

        Args:
            soft_limits (bool): use software limits or not
        """
        self.soft_limits = soft_limits
   

    def set_velocity_parameters(self,
                                acceleration = None,
                                max_velocity = None,
                                channel      = 1):
        """Sets the trapezoidal velocity parameters of the controller

        Sets the trapezoidal velocity parameters of the controller. Note that
        minimum velocity cannot be set, because protocol demands it is always
        zero.
   
        When called without arguments, max acceleration and max velocity will
        be set to self.max_acceleration and self.max_velocity

        If parameters exeed self.max_velocity or self.max_acceleration resp.
        the will be clamped to that maximum value

        Args:
              acceleration (float): acceleration parameter in mm/s^2
              max_velocity (float): maximum velocity parameter in mm/s
              channel (int): channel of device (multi-channel controllers only)
        """

        if acceleration == None:
          acceleration = self.max_acceleration
   
        if max_velocity == None:
          max_velocity = self.max_velocity
   
        # software limiting again for extra safety
        acceleration = min(acceleration, self.max_acceleration)
        max_velocity = min(max_velocity, self.max_velocity)
   
        acc_apt = int(acceleration * self.acceleration_scale)
        max_vel_apt = int(max_velocity * self.velocity_scale)
   
        # <: small endian
        # H: 2 bytes for channel
        # i: 4 bytes for min velocity
        # i: 4 bytes for acceleration
        # i: 4 bytes for max velocity
        params = st.pack('<Hiii', channel, 0, acc_apt, max_vel_apt)
        setmsg = Message(message.MGMSG_MOT_SET_VELPARAMS, data=params)
        self._send_message(setmsg)
   

    def velocity_parameters(self, channel=1, raw=False):
        """Returns the trapezoidal velocity parameters of the controller

        Returns the trapezoidal velocity parameters of the controller, that is
        minimum start velocity, acceleration, and maximum velocity. All of which
        are returned in realworld units.

        Example:
            min_vel, acc, max_vel = con.velocity_parameters()

        Args:
              channel (int): channel of device (multi-channel controllers only)
              raw (bool): If True do not convert parameters to SI unit scale

        Returns:
            float: minimum velocity in mm/s
            float: acceleration in mm/s^2
            float: maximum velocity in mm/s
        """

        reqmsg = Message(message.MGMSG_MOT_REQ_VELPARAMS, param1=channel)
        self._send_message(reqmsg)
   
        getmsg = self._wait_message(message.MGMSG_MOT_GET_VELPARAMS)
   
        # <: small endian
        # H: 2 bytes for channel
        # i: 4 bytes for min velocity
        # i: 4 bytes for acceleration
        # i: 4 bytes for max velocity
        ch,min_vel,acc,max_vel = st.unpack('<Hiii',getmsg.datastring)
   
        if not raw:
            min_vel /= self.velocity_scale
            max_vel /= self.velocity_scale
            acc     /= self.acceleration_scale
   
        return min_vel, acc, max_vel
   

    def info(self):
        """Get hardware info of the controller

        The hardware info is returned as a tuple containing these fields:
          - serial number
          - model number
          - hardware type, either 45 for multi-channel motherboard, or 44 for
            brushless DC motor
          - firmware version as major.interim.minor
          - notes
          - hardware version number
          - modification state of controller
          - number of channels

        Returns:
            tuple: tuple containing hardware information fields
        """
   
        reqmsg = Message(message.MGMSG_HW_REQ_INFO)
        self._send_message(reqmsg)
   
        getmsg = self._wait_message(message.MGMSG_HW_GET_INFO)

        # <: small endian
        # I:    4 bytes for serial number
        # 8s:   8 bytes for model number
        # H:    2 bytes for hw type
        # 4s:   4 bytes for firmware version
        # 48s:  48 bytes for notes
        # 12s:  12 bytes of empty space
        # H:    2 bytes for hw version
        # H:    2 bytes for modificiation state
        # H:    2 bytes for number of channels
        info = st.unpack('<I8sH4s48s12sHHH', getmsg.datastring)
   
        sn,model,hwtype,fwver,notes,_,hwver,modstate,numchan = info
        fwver = '%d.%d.%d' % (fwver[2],fwver[1],fwver[0])
   
        return (sn,model,hwtype,fwver,notes,hwver,modstate,numchan)
   

    def stop(self, channel=1, immediate=False, wait=True):
        """Stops the motor on the specified channel

        Stops the motor on the specified channel. If immediate is True, then
        the motor stops immediately, otherwise it stops in a profiled manner,
        i.e.  decelerates accoding to max acceleration from current velocity
        down to zero
   
        If wait is True, then this method returns only when
        MGMSG_MOT_MOVE_STOPPED is read, and controller reports velocity of 0.
   
        Args:
            channel (int): channel of device (multi-channel controllers only)
            immediate (bool): stop immediately without profiled deceleration
            wait (bool): When wait is True, this method only returns when the
                         stage has signaled STOPPED and its velocity is 0

        Returns:
            ControllerStatus: only if wait is true, None otherwise
        """
   
        if wait:
            self.resume_end_of_move_messages()
        else:
            self.suspend_end_of_move_messages()
   
        stopmsg = Message(message.MGMSG_MOT_MOVE_STOP,
                          param1 = channel,
                          param2 = int(immediate))
        self._send_message(stopmsg)
   
        if wait:
            self._wait_message(message.MGMSG_MOT_MOVE_STOPPED)
            sts = self.status()
            while sts.velocity_apt:
                time.sleep(0.001)
                sts = self.status()
            return sts
        else:
          return None
   

    def keepalive(self):
        """Sends a keep_alive signal to the device

        This sends MGMSG_MOT_ACK_DCSTATUSUPDATE to the controller to keep it
        from going dark. Per documentation:
            If using the USB port, this message called "server alive" must be
            sent by the server to the controller at least once a second or the
            controller will stop responding after ~50 commands
        However, in field tests this behaviour has not been observed.
        """
        msg = Message(message.MGMSG_MOT_ACK_DCSTATUSUPDATE)
        self._send_message(msg)





class ControllerStatus(object):
    """This class encapsulate the controller status, which includes its position,
    velocity, and various flags.
   
    The position and velocity properties will return realworld values of 
    mm and mm/s respectively.
    """
   
    def __init__(self, controller, statusbytestring):
        """Constructor

        Construct an instance of ControllerStatus from the 14 byte status sent
        by the controller which contains the current position encoder count,
        the actual velocity, scaled, and statusbits.

        Args:
            controller (Controller): instance of the stage controller
            statusbytestring (bytes): byte string containing status information
        """
   
        super(ControllerStatus, self).__init__()
   
        # <: little endian
        # H: 2 bytes for channel ID
        # i: 4 bytes for position counter
        # h: 2 bytes for velocity
        # H: 2 bytes reserved
        # I: 4 bytes for status
        # Note that velocity in the docs is stated as a unsigned word, by in
        # reality it looks like it is signed.
        channel, pos_apt, vel_apt, _, statusbits = st.unpack('<HihHI',
                                                             statusbytestring)
   
        self.channel = channel
        if pos_apt:
            self.position = float(pos_apt) / controller.position_scale
        else:
            self.position = 0
   
        # XXX the protocol document, revision 7, is explicit about the scaling
        # Note that I don't trust this value, because the measured velocity
        # does not correspond to the value from the scaling. The value used here
        # is derived from trial and error
        if vel_apt:
            self.velocity = float(vel_apt) / 10
        else:
            self.velocity = 0
   
        self.statusbits = statusbits
   
        # save the "raw" controller values since they are convenient for
        # zero-checking
        self.position_apt = pos_apt
        self.velocity_apt = vel_apt
   

    @property
    def forward_hardware_limit_switch_active(self):
        return self.statusbits & 0x01
   

    @property
    def reverse_hardware_limit_switch_active(self):
        return self.statusbits & 0x02
   

    @property
    def moving(self):
        return self.moving_forward or self.moving_reverse


    @property
    def moving_forward(self):
        return self.statusbits & 0x10
   

    @property
    def moving_reverse(self):
        return self.statusbits & 0x20
   

    @property
    def jogging_forward(self):
        return self.statusbits & 0x40
   

    @property
    def jogging_reverse(self):
        return self.statusbits & 0x80
   

    @property
    def homing(self):
        return self.statusbits & 0x200
   

    @property
    def homed(self):
        return self.statusbits & 0x400
   

    @property
    def tracking(self):
        return self.statusbits & 0x1000
   

    @property
    def settled(self):
        return self.statusbits & 0x2000
   

    @property
    def excessive_position_error(self):
        """This flag means that there is excessive positioning error, and the
        stage should be re-homed. This happens if while moving the stage is
        impeded, and where it thinks it is isn't where it is
        """
        return self.statusbits & 0x4000
   

    @property
    def motor_current_limit_reached(self):
        return self.statusbits & 0x01000000
   

    @property
    def channel_enabled(self):
        return self.statusbits & 0x80000000
   
   
    @property
    def shortstatus(self):
        """Returns a short, fixed width, status line

        Returns a short, fixed width, status line that shows whether the
        controller is moving, the direction, whether it has been homed, and
        whether excessive position error is present.
   
        These are shown via the following letters:
            H: homed
            M: moving
            T: tracking
            S: settled
            F: forward limit switch tripped
            R: reverse limit switch tripped
            E: excessive position error
   
        Format of the string is as follows:
          H MTS FRE
   
        Each letter may or may not be present.  When a letter is present, it is
        a positive indication of the condition.
   
        Example:
            "H M-- ---" means homed, moving
            "H M-- --E" means homed, moving reverse, excessive position error

        Returns:
            str: status line string
        """

        shortstat = []
        def add(flag, letter):
            if flag:
                shortstat.append(letter)
            else:
                shortstat.append('-')
   
        sep = ' '
        add(self.homed, 'H')
   
        shortstat.append(sep)
   
        add(self.moving,   'M')
        add(self.tracking, 'T')
        add(self.settled,  'S')
   
        shortstat.append(sep)
   
        add(self.forward_hardware_limit_switch_active, 'F')
        add(self.reverse_hardware_limit_switch_active, 'R')
        add(self.excessive_position_error,             'E')
   
        return ''.join(shortstat)
   

    def flag_strings(self):
        """Returns the various flags as user readable strings

        Returns:
            list: status flags a list of string descriptions
        """

        masks={ 0x01:       'Forward hardware limit switch active',
                0x02:       'Reverse hardware limit switch active',
                0x10:       'In motion, moving forward',
                0x20:       'In motion, moving backward',
                0x40:       'In motion, jogging forward',
                0x80:       'In motion, jogging backward',
                0x200:      'In motion, homing',
                0x400:      'Homed',
                0x1000:     'Tracking',
                0x2000:     'Settled',
                0x4000:     'Excessive position error',
                0x01000000: 'Motor current limit reached',
                0x80000000: 'Channel enabled'
                }
        statuslist = []
        for bitmask in masks:
            if self.statusbits & bitmask:
                statuslist.append(masks[bitmask])
      
        return statuslist
   

    def __str__(self):
        return 'pos=%.2fmm vel=%.2fmm/s, flags=%s' \
            % (self.position, self.velocity, self.flag_strings())
   
