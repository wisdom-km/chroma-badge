#pragma once

#include <cstdint>

namespace nfc {

constexpr uint8_t ADDR_USER = 0x53;  // ST25DV user memory, E2=1
constexpr uint8_t ADDR_SYS  = 0x57;

void begin();
bool present();  // ACK on user-area address

}  // namespace nfc
