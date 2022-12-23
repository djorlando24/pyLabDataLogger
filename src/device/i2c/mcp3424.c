/*
    MCP3424 I2C Analog to Digital Converter
    Software based on https://github.com/alxyng/mcp3424
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2023 LTRAC
    @license GPL-3.0+
    @version 1.3.0
    @date 23/12/2022
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

#include <errno.h>
#include <linux/i2c-dev.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdlib.h>
#include "mcp3424.h"

static void mcp3424_set_errstr(mcp3424 *m, const char *format, ...) {
	va_list ap;
	va_start(ap, format);
	vsnprintf(m->errstr, MCP3424_ERR_LEN, format, ap);
	va_end(ap);
}

static void mcp3424_set_channel(mcp3424 *m, enum mcp3424_channel channel) {
	m->config &= ~0x60;
	m->config |= (channel << 5);
}

void mcp3424_init(mcp3424 *m, char *dev, uint8_t addr, enum mcp3424_resolution res) {
	m->fd = open(dev, O_RDWR);
        if ( m->fd == -1 ) return;
	//m->fd = fd;
	m->addr = addr;
	m->config = 0x00;
	m->err = MCP3424_OK;
	mcp3424_set_channel(m, MCP3424_CHANNEL_1);
	mcp3424_set_conversion_mode(m, MCP3424_CONVERSION_MODE_ONE_SHOT);
	mcp3424_set_pga(m, MCP3424_PGA_1X);
	mcp3424_set_resolution(m, res);
}

void mcp3424_close(mcp3424 *m) {
	close(m->fd);
}

void mcp3424_set_conversion_mode(mcp3424 *m, enum mcp3424_conversion_mode mode) {
	m->config &= ~0x10;
	m->config |= (mode << 4);
}

void mcp3424_set_pga(mcp3424 *m, enum mcp3424_pga pga) {
	m->config &= ~0x03;
	m->config |= pga;
}

void mcp3424_set_resolution(mcp3424 *m, enum mcp3424_resolution res) {
	m->config &= ~0x0c;
	m->config |= (res << 2);
}

enum mcp3424_conversion_mode mcp3424_get_conversion_mode(mcp3424 *m) {
	return (m->config >> 4) & 0x03;
}

enum mcp3424_pga mcp3424_get_pga(mcp3424 *m) {
	return m->config & 0x03;
}

enum mcp3424_resolution mcp3424_get_resolution(mcp3424 *m) {
	return (m->config >> 2) & 0x03;
}

unsigned int mcp3424_get_raw(mcp3424 *m, enum mcp3424_channel channel) {
	int rv;
	ssize_t n;
	uint8_t reading[4];
	unsigned int raw;

	rv = ioctl(m->fd, I2C_SLAVE, m->addr);
	if (rv == -1) {
		mcp3424_set_errstr(m, "ioctl: %s", strerror(errno));
		m->err = MCP3424_ERR;
		return 0;
	}

	mcp3424_set_channel(m, channel);

	// if one shot, write ready bit to start new conversion on mcp3424
	if (mcp3424_get_conversion_mode(m) == MCP3424_CONVERSION_MODE_ONE_SHOT) {
		m->config |= (1 << 7);
	}
 
	n = write(m->fd, &m->config, 1);
	if (n < 1) {
		if (n == 0) {
			mcp3424_set_errstr(m, "failed to write config byte");
			m->err = MCP3424_WARN;
		} else if (n == -1) {
			mcp3424_set_errstr(m, "write: %s", strerror(errno));
			m->err = MCP3424_ERR;
		}
		return 0;
	}

	if (mcp3424_get_conversion_mode(m) == MCP3424_CONVERSION_MODE_ONE_SHOT) {
		m->config &= ~(1 << 7);
	}

	while (1) {
		n = read(m->fd, reading, 4);
		if (n < 4) {
			if (n >= 0) {
				mcp3424_set_errstr(m, "failed to read 4 byte reading");
				m->err = MCP3424_WARN;
			} else if (n == -1) {
				mcp3424_set_errstr(m, "read: %s", strerror(errno));
				m->err = MCP3424_ERR;
			}
			return 0;
		}

		// loop until ready bit is 0 (new reading)
		if (mcp3424_get_resolution(m) == MCP3424_RESOLUTION_18) {
			if ((reading[3] >> 7) == 0) {
				break;
			}
		} else {
			if ((reading[2] >> 7) == 0) {
				break;
			}
		}
	}

	switch (mcp3424_get_resolution(m)) {
		case MCP3424_RESOLUTION_12:
			raw = ((reading[0] & 0x0f) << 8) | reading[1];
			break;
		case MCP3424_RESOLUTION_14:
			raw = ((reading[0] & 0x3f) << 8) | reading[1];
			break;
		case MCP3424_RESOLUTION_16:
			raw = (reading[0] << 8) | reading[1];
			break;
		case MCP3424_RESOLUTION_18:
			raw = ((reading[0] & 0x03) << 16) | (reading[1] << 8) | reading[2];
			break;
		default:
			mcp3424_set_errstr(m, "invalid resolution");
			m->err = MCP3424_ERR;
			return 0;
	}

	return raw;
}
