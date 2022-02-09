#ifndef MCP3424_H_
#define MCP3424_H_

#include <stdint.h>

#define MCP3424_OK 0
#define MCP3424_ERR -1
#define MCP3424_WARN -2
#define MCP3424_ERR_LEN 256

enum mcp3424_channel {
	MCP3424_CHANNEL_1,
	MCP3424_CHANNEL_2,
	MCP3424_CHANNEL_3,
	MCP3424_CHANNEL_4
};

enum mcp3424_conversion_mode {
	MCP3424_CONVERSION_MODE_ONE_SHOT,
	MCP3424_CONVERSION_MODE_CONTINUOUS
};

enum mcp3424_pga {
	MCP3424_PGA_1X,
	MCP3424_PGA_2X,
	MCP3424_PGA_4X,
	MCP3424_PGA_8X
};

enum mcp3424_resolution {
	MCP3424_RESOLUTION_12,
	MCP3424_RESOLUTION_14,
	MCP3424_RESOLUTION_16,
	MCP3424_RESOLUTION_18
};

typedef struct {
	int fd;
	uint8_t addr;
	uint8_t config;
	int err;
	char errstr[MCP3424_ERR_LEN];
} mcp3424;

void mcp3424_init(mcp3424 *m, int fd, uint8_t addr, enum mcp3424_resolution res);

void mcp3424_set_conversion_mode(mcp3424 *m, enum mcp3424_conversion_mode mode);
void mcp3424_set_pga(mcp3424 *m, enum mcp3424_pga pga);
void mcp3424_set_resolution(mcp3424 *m, enum mcp3424_resolution res);

enum mcp3424_conversion_mode mcp3424_get_conversion_mode(mcp3424 *m);
enum mcp3424_pga mcp3424_get_pga(mcp3424 *m);
enum mcp3424_resolution mcp3424_get_resolution(mcp3424 *m);

unsigned int mcp3424_get_raw(mcp3424 *m, enum mcp3424_channel channel);

#endif /* MCP3424_H_ */
