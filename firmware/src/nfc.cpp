#include "nfc.h"

#include "pins.h"

#include <Wire.h>

namespace nfc {

void begin() {
    Wire.begin(pins::I2C_SDA, pins::I2C_SCL);
    Wire.setClock(100000);
}

bool present() {
    Wire.beginTransmission(ADDR_USER);
    return Wire.endTransmission() == 0;
}

}  // namespace nfc
